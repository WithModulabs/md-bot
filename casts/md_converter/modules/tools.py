"""Tools used by StructureAnalyzerAgent to detect document structure elements."""

import re

from langchain.tools import tool


@tool
def detect_headings(raw_content: str) -> str:
    """Detect heading candidates in raw document text.

    Looks for lines that are short (≤120 chars), capitalised, or follow common
    heading patterns (ALL CAPS, Title Case, numbered like "1." / "1.1").

    Args:
        raw_content: Raw text extracted from the document.

    Returns:
        JSON array string of heading candidates with estimated level and text.
    """
    import json

    lines = raw_content.splitlines()
    headings = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) > 120:
            continue
        level = None
        # Numbered heading: "1. Title", "1.1 Title", "1.1.1 Title"
        if re.match(r"^\d+(\.\d+){0,2}[\s\.\)]\s*\S", stripped):
            depth = stripped.split()[0].count(".")
            level = min(depth + 1, 6)
        # ALL CAPS short line
        elif stripped.isupper() and len(stripped) > 3:
            level = 1
        # Title Case short line (no sentence-ending punctuation)
        elif (
            stripped.istitle()
            and not stripped.endswith((".", ",", ";", ":"))
            and len(stripped.split()) <= 10
        ):
            level = 2
        if level is not None:
            headings.append({"level": level, "text": stripped, "position": i})
    return json.dumps(headings)


@tool
def detect_tables(raw_content: str) -> str:
    """Detect tabular data in raw document text.

    Identifies pipe-delimited rows or consistent whitespace-aligned columns
    spanning multiple lines.

    Args:
        raw_content: Raw text extracted from the document.

    Returns:
        JSON array string where each entry has 'headers' and 'rows'.
    """
    import json

    lines = raw_content.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Pipe-delimited table
        if "|" in line and line.count("|") >= 2:
            block = []
            while i < len(lines) and "|" in lines[i]:
                block.append([c.strip() for c in lines[i].split("|") if c.strip()])
                i += 1
            if len(block) >= 2:
                headers = block[0]
                rows = [r for r in block[1:] if not all(set(c) <= set("-:") for c in r)]
                tables.append({"headers": headers, "rows": rows})
            continue
        i += 1
    return json.dumps(tables)


@tool
def detect_code_blocks(raw_content: str) -> str:
    """Detect code snippets or command examples in raw document text.

    Looks for lines with consistent leading whitespace (≥4 spaces), fence
    markers (```), or common shell/code patterns.

    Args:
        raw_content: Raw text extracted from the document.

    Returns:
        JSON array string where each entry has 'language' and 'content'.
    """
    import json

    blocks = []
    # Fenced code blocks
    fenced = re.findall(r"```(\w*)\n(.*?)```", raw_content, re.DOTALL)
    for lang, content in fenced:
        blocks.append({"language": lang or "text", "content": content.strip()})

    # Indented blocks (4+ spaces, 2+ consecutive lines)
    lines = raw_content.splitlines()
    indented_buf: list[str] = []
    for line in lines:
        if line.startswith("    ") or line.startswith("\t"):
            indented_buf.append(line.strip())
        else:
            if len(indented_buf) >= 2:
                blocks.append({"language": "text", "content": "\n".join(indented_buf)})
            indented_buf = []
    if len(indented_buf) >= 2:
        blocks.append({"language": "text", "content": "\n".join(indented_buf)})

    return json.dumps(blocks)


@tool
def detect_lists(raw_content: str) -> str:
    """Detect bullet and numbered lists in raw document text.

    Args:
        raw_content: Raw text extracted from the document.

    Returns:
        JSON array string where each entry has 'ordered' (bool) and 'items' (list[str]).
    """
    import json

    lines = raw_content.splitlines()
    lists = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Unordered list
        if re.match(r"^[-*•]\s+\S", line):
            items = []
            while i < len(lines) and re.match(r"^[-*•]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*•]\s+", "", lines[i].strip()))
                i += 1
            if items:
                lists.append({"ordered": False, "items": items})
            continue
        # Ordered list
        if re.match(r"^\d+[.)]\s+\S", line):
            items = []
            while i < len(lines) and re.match(r"^\d+[.)]\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+[.)]\s+", "", lines[i].strip()))
                i += 1
            if items:
                lists.append({"ordered": True, "items": items})
            continue
        i += 1
    return json.dumps(lists)
