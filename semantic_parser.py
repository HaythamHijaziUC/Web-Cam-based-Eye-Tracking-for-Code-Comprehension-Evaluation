def parse_semantic_regions(lines):
    regions = []
    current = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Start of a function
        if stripped.startswith("def "):
            if current:
                regions.append(current)
            current = {"name": stripped, "start": i, "end": i}

        # Start of class
        elif stripped.startswith("class "):
            if current:
                regions.append(current)
            current = {"name": stripped, "start": i, "end": i}

        # Loop blocks
        elif stripped.startswith("for ") or stripped.startswith("while "):
            if current:
                regions.append(current)
            current = {"name": stripped, "start": i, "end": i}

        # If/elif/else blocks
        elif stripped.startswith("if ") or stripped.startswith("elif ") or stripped.startswith("else"):
            if current:
                regions.append(current)
            current = {"name": stripped, "start": i, "end": i}

        # Extend current region
        if current:
            current["end"] = i

    if current:
        regions.append(current)

    return regions
