import ast
import re

def parse_semantic_regions(code_content, file_ext=".py", max_lines=14):
    """
    Parses code based on file extension.
    Supports Python AST and a generic fallback for others.
    Ensures non-overlapping, size-capped regions (e.g. <= 14 lines max).
    """
    if file_ext == ".py":
        return _parse_python_ast(code_content, max_lines)
    else:
        return _parse_generic_fallback(code_content, max_lines)

def _parse_python_ast(code_content, max_lines):
    try:
        tree = ast.parse(code_content)
    except Exception as e:
        print(f"AST Parsing error: {e}")
        return _parse_generic_fallback(code_content, max_lines)

    regions = []

    def process_body(statements, parent_name):
        current_region = []
        current_start = -1
        current_end = -1
        
        for stmt in statements:
            stmt_start = getattr(stmt, 'lineno', -1)
            stmt_end = getattr(stmt, 'end_lineno', -1)
            if stmt_start == -1: 
                continue

            # Check if this single statement is a compound statement that exceeds max_lines
            is_compound = hasattr(stmt, 'body')
            if is_compound and (stmt_end - stmt_start + 1) > max_lines:
                # Flush the current region
                if current_region:
                    regions.append({
                        "name": f"{parent_name} [{current_start}-{current_end}]",
                        "start": current_start - 1,
                        "end": current_end - 1
                    })
                    current_region = []
                
                # Define a name for the compound header
                stmt_name = type(stmt).__name__
                if hasattr(stmt, 'name'):
                    stmt_name = f"{stmt_name} ({stmt.name})"
                
                # The header is from stmt_start to the line before body starts
                header_end = stmt.body[0].lineno - 1
                if header_end >= stmt_start:
                    regions.append({
                        "name": f"{stmt_name} Header",
                        "start": stmt_start - 1,
                        "end": header_end - 1
                    })
                
                # Recursively process the body
                process_body(stmt.body, stmt_name)
                
                # Process orelse (if/for/while) branch
                if hasattr(stmt, 'orelse') and stmt.orelse:
                    orelse_start = stmt.orelse[0].lineno - 1
                    header_orelse_start = stmt.body[-1].end_lineno
                    if orelse_start > header_orelse_start:
                        regions.append({
                            "name": f"{stmt_name} Branch Header",
                            "start": header_orelse_start,
                            "end": orelse_start - 1
                        })
                    process_body(stmt.orelse, f"{stmt_name} Branch")
            
            else:
                if not current_region:
                    current_start = stmt_start
                
                if (stmt_end - current_start + 1) > max_lines and current_region:
                    # Flush current
                    regions.append({
                        "name": f"{parent_name} [{current_start}-{current_end}]",
                        "start": current_start - 1,
                        "end": current_end - 1
                    })
                    current_region = [stmt]
                    current_start = stmt_start
                    current_end = stmt_end
                else:
                    current_region.append(stmt)
                    current_end = max(current_end, stmt_end)

        if current_region:
            regions.append({
                "name": f"{parent_name} [{current_start}-{current_end}]",
                "start": current_start - 1,
                "end": current_end - 1
            })

    process_body(tree.body, "Module")
    
    # Sort regions
    regions.sort(key=lambda x: x["start"])
    
    # Fix potential 1-line overlaps edge cases (due to multiline string AST offsets, etc.)
    for i in range(len(regions) - 1):
        if regions[i]["end"] >= regions[i+1]["start"]:
            regions[i]["end"] = regions[i+1]["start"] - 1

    # Remove empty regions
    regions = [r for r in regions if r["end"] >= r["start"]]
    return regions

def _parse_generic_fallback(code_content, max_lines):
    lines = code_content.splitlines()
    regions = []
    for i in range(0, len(lines), max_lines):
        chunk_end = min(i + max_lines - 1, len(lines) - 1)
        regions.append({
            "name": f"Chunk [{i+1}-{chunk_end+1}]",
            "start": i,
            "end": chunk_end
        })
    return regions
