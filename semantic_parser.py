import ast
import re

def parse_semantic_regions(code_content, file_ext=".py"):
    """
    Parses code based on file extension.
    Supports Python AST and a generic fallback for others.
    """
    if file_ext == ".py":
        return _parse_python_ast(code_content)
    else:
        return _parse_generic_fallback(code_content)

def _parse_python_ast(code_content):
    try:
        tree = ast.parse(code_content)
    except Exception as e:
        print(f"AST Parsing error: {e}")
        return _parse_generic_fallback(code_content)

    regions = []

    class RegionVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            regions.append({"name": f"Function: {node.name}", "start": node.lineno - 1, "end": node.end_lineno - 1})
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            regions.append({"name": f"Class: {node.name}", "start": node.lineno - 1, "end": node.end_lineno - 1})
            self.generic_visit(node)

        def visit_For(self, node):
            regions.append({"name": "For Loop", "start": node.lineno - 1, "end": node.end_lineno - 1})
            self.generic_visit(node)

        def visit_While(self, node):
            regions.append({"name": "While Loop", "start": node.lineno - 1, "end": node.end_lineno - 1})
            self.generic_visit(node)

        def visit_If(self, node):
            regions.append({"name": "If Block", "start": node.lineno - 1, "end": node.end_lineno - 1})
            self.generic_visit(node)

    visitor = RegionVisitor()
    visitor.visit(tree)
    regions.sort(key=lambda x: x["start"])
    return regions

def _parse_generic_fallback(code_content):
    """
    A simple indentation-based or keyword-based fallback for C++/Java.
    """
    lines = code_content.splitlines()
    regions = []
    
    # Very basic regex for common patterns in Java/C++
    patterns = {
        "Function/Method": r"(public|private|static|\w+)\s+\w+\s*\([^)]*\)\s*\{",
        "If Block": r"if\s*\([^)]*\)\s*\{",
        "Loop": r"(for|while)\s*\([^)]*\)\s*\{"
    }

    current = None
    for i, line in enumerate(lines):
        for label, pattern in patterns.items():
            if re.search(pattern, line):
                if current:
                    regions.append(current)
                current = {"name": f"{label} (Line {i+1})", "start": i, "end": i}
                break
        
        if current:
            current["end"] = i
            
    if current:
        regions.append(current)
        
    return regions
