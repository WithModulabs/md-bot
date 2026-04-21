<!-- AUTO-MANAGED: act-overview -->
## Act Overview

**md-bot** is a document processing pipeline that converts any input document into clean, well-structured Markdown files. Given a file path (PDF, DOCX, HTML, PPTX, image, or plain text), the Act extracts content, uses an AI agent to interpret the document structure, and writes a `.md` output file.

**Domain:** Document Processing / Content Transformation

<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: casts-table -->
## Casts

| Cast | Description | Pattern |
|------|-------------|---------|
| [md_converter](./casts/md_converter/CLAUDE.md) | Converts any document format to Markdown | Branching + Sequential |

<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: project-structure -->
## Project Structure

```
md-bot/
├── CLAUDE.md
├── pyproject.toml
├── langgraph.json
├── casts/
│   ├── base_graph.py
│   ├── base_node.py
│   └── md_converter/
│       ├── pyproject.toml
│       ├── graph.py
│       └── modules/
│           ├── state.py
│           ├── models.py
│           ├── tools.py
│           ├── agents.py
│           ├── nodes.py
│           ├── conditions.py
│           └── prompts.py
└── tests/
    └── cast_tests/
        └── md_converter_test.py
```

<!-- END AUTO-MANAGED -->

<!-- AUTO-MANAGED: development-commands -->
## Development Commands

```bash
# Start development server
uv run langgraph dev

# Sync dependencies
uv sync

# Create a new cast
uv run act cast -c "<cast_name>"

# Add a dependency to a cast
uv add --package <cast_name> <package>
```

<!-- END AUTO-MANAGED -->

<!-- MANUAL -->
## Notes

Add project-specific notes here. This section is never auto-modified.

<!-- END MANUAL -->
