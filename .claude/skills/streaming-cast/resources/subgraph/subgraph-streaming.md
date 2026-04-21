# Subgraph Streaming

Stream events from nested subgraphs within the graph using `subgraphs=True`.

## Contents

- Enable Subgraph Streaming
- Namespace Identification
- Filter Parent vs Child

## Enable Subgraph Streaming

By default, streaming only shows root graph events. Add `subgraphs=True`:

```python
graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages",
    subgraphs=True,
    version="v2",
):
    if chunk["ns"]:
        # Event from a subgraph/subagent
        source = _parse_source(chunk["ns"])
    else:
        # Root graph event
        source = "root"
```

---

## Namespace Identification

The `ns` field is a tuple identifying the event source:

| `ns` value | Source |
|------------|--------|
| `()` | Root graph |
| `("NodeName:<task_id>",)` | Direct subgraph/agent |
| `("NodeName:<id>", "tools:<id>")` | Tool execution within agent |
| `("NodeName:<id>", "tools:<id>", "subagent:<id>")` | Subagent model call |
| `("NodeName:<id>", "tools:<id>", "subagent:<id>", "tools:<id2>")` | Subagent tool execution |

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    depth = len(chunk["ns"])

    if depth == 0:
        print(f"[Root] ...")
    elif depth == 1:
        name = chunk["ns"][0].split(":")[0]
        print(f"[{name}] ...")
    else:
        path = " → ".join(ns.split(":")[0] for ns in chunk["ns"])
        print(f"[{path}] ...")
```

---

## Filter Parent vs Child

### Only Root Events

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if not chunk["ns"]:
        msg, metadata = chunk["data"]
        # ...
```

### Only Subgraph Events

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["ns"]:
        msg, metadata = chunk["data"]
        source = _parse_source(chunk["ns"])
        # ...
```

### Specific Subgraph

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["ns"] and chunk["ns"][0].startswith("researcher"):
        msg, metadata = chunk["data"]
        # ...
```
