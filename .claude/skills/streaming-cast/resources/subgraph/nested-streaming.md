# Namespace Parsing

Parse multi-level namespace tuples to identify event sources in nested graphs.

## Contents

- Namespace Structure
- _parse_source Pattern
- Utility Dataclass
- Visualization

## Namespace Structure

When a graph contains subgraphs, agents, or subagents internally, `subgraphs=True` produces multi-level namespaces:

```
Root graph  ()
└─ Agent    ("AgentNode:<id>",)
   ├─ tool  ("AgentNode:<id>", "tools:<id>")
   └─ sub   ("AgentNode:<id>", "tools:<id>", "researcher:<id>")
      └─ tool ("AgentNode:<id>", "tools:<id>", "researcher:<id>", "tools:<id2>")
```

**Rule:** `"tools:"` segments mark tool execution boundaries. The segment after a `"tools:"` boundary is the subagent name.

---

## _parse_source Pattern

Extract the agent/subagent name from a namespace tuple:

```python
def _parse_source(ns: tuple[str, ...]) -> str:
    """Extract agent source name from v2 namespace tuple.

    Scans past the first segment (outer node), looks for a "tools:"
    boundary, then returns the first non-tools segment after it
    as the subagent name.
    """
    if len(ns) <= 1:
        return "oke"

    found_tools = False
    for seg in ns[1:]:
        name = seg.split(":")[0] if ":" in seg else seg
        if name == "tools":
            found_tools = True
            continue
        if found_tools:
            return name

    return "oke"
```

Usage:

```python
graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue

    msg, metadata = chunk["data"]
    source = _parse_source(chunk["ns"])

    if msg.content and metadata.get("langgraph_node") == "model":
        await send({"type": "token", "content": msg.content, "source": source})
```

---

## Utility Dataclass

For complex namespace handling:

```python
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class StreamSource:
    """Parsed namespace identifying a streaming event source."""
    depth: int
    path: tuple[str, ...]
    is_root: bool
    is_subagent: bool
    call_ids: tuple[str, ...]


def parse_namespace(ns: tuple[str, ...]) -> StreamSource:
    """Parse a v2 StreamPart namespace tuple."""
    names = tuple(part.split(":")[0] for part in ns)
    call_ids = tuple(part.split(":")[1] if ":" in part else "" for part in ns)

    return StreamSource(
        depth=len(ns),
        path=names,
        is_root=len(ns) == 0,
        is_subagent=any(n == "tools" for n in names),
        call_ids=call_ids,
    )
```

---

## Visualization

Print a tree-structured view of streaming events:

```python
seen_namespaces: set[tuple[str, ...]] = set()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="updates", subgraphs=True, version="v2",
):
    ns_key = chunk["ns"]

    if ns_key not in seen_namespaces:
        seen_namespaces.add(ns_key)
        depth = len(ns_key)
        if depth > 0:
            name = ns_key[-1].split(":")[0]
            prefix = "│ " * (depth - 1) + "├─ "
            print(f"{prefix}{name}")

    depth = len(ns_key)
    indent = "│ " * depth + "  "
    for node, state in chunk["data"].items():
        print(f"{indent}[{node}] {list(state.keys())}")
```

Output:
```
[preprocess] ['prepared_input']
├─ AgentNode
│   [model] ['messages']
│   ├─ tools
│   │   [researcher] ['result']
[postprocess] ['final_result']
```
