# StreamPart Format

Every v2 streaming chunk is a typed dict. Common keys: `type`, `ns`, `data`.

## Contents

- Structure
- Data Shape by Type
- Type Narrowing
- Import Types

## Structure

```python
{
    "type": "values" | "updates" | "messages" | "custom" | "checkpoints" | "tasks" | "debug",
    "ns": (),          # namespace tuple — empty for root graph
    "data": ...        # payload, varies by type
}
```

| Key | Type | Description |
|-----|------|-------------|
| `type` | `str` | Stream mode that produced this chunk |
| `ns` | `tuple[str, ...]` | Namespace identifying source. `()` = root, `("Node:<id>",)` = subgraph/agent |
| `data` | varies | Payload — see Data Shape by Type below |
| `interrupts` | `tuple[Interrupt, ...]` | **Only on `"values"` type** — interrupts triggered during the step |

---

## Data Shape by Type

| Type | `data` shape | Extra keys | Notes |
|------|-------------|------------|-------|
| `"values"` | `OutputT` (full state dict/model) | `interrupts` | `__interrupt__` is popped from data into `interrupts` field |
| `"updates"` | `dict[str, Any]` (node→output) | — | May contain `__interrupt__` and `__metadata__` keys in data |
| `"messages"` | `tuple[BaseMessage, dict]` | — | `(message_chunk, metadata)` where metadata has `langgraph_node`, `langgraph_step`, etc. |
| `"custom"` | `Any` | — | Whatever was passed to `StreamWriter` |
| `"checkpoints"` | `CheckpointPayload` | — | Same format as `get_state()`. State values are coerced via output mapper |
| `"tasks"` | `TaskPayload \| TaskResultPayload` | — | Start: `id`, `name`, `input`, `triggers`. Result: `id`, `name`, `error`, `interrupts`, `result` |
| `"debug"` | `DebugPayload` | — | Wraps checkpoint with `{"type": "checkpoint", "payload": {...}}`. State values coerced |

---

## Type Narrowing

Filtering by `chunk["type"]` automatically narrows the `data` type:

```python
from casts.oke.graph import oke_graph

graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=["messages", "updates", "custom"],
    subgraphs=True, version="v2",
):
    if chunk["type"] == "messages":
        # MessagesStreamPart — data is (token, metadata) tuple
        msg, metadata = chunk["data"]
        if msg.content:
            print(msg.content, end="")

    elif chunk["type"] == "values":
        # ValuesStreamPart — data is full state dict
        # Also includes "interrupts" key: tuple of Interrupt objects
        state = chunk["data"]
        interrupts = chunk.get("interrupts", ())
        if interrupts:
            print(f"Interrupts: {interrupts}")

    elif chunk["type"] == "updates":
        # UpdatesStreamPart — data is {node_name: {updated_keys}}
        # May also contain "__interrupt__" and "__metadata__" keys
        for key, value in chunk["data"].items():
            if key == "__interrupt__":
                print(f"Interrupts: {value}")
            elif key == "__metadata__":
                continue
            else:
                print(f"{key}: {value}")

    elif chunk["type"] == "custom":
        # CustomStreamPart — data is whatever the node's writer sent
        print(f"Custom: {chunk['data']}")
```

---

## Import Types

```python
from langgraph.types import (
    StreamPart,            # Union of all stream part types
    ValuesStreamPart,
    UpdatesStreamPart,
    MessagesStreamPart,
    CustomStreamPart,
    CheckpointStreamPart,
    TasksStreamPart,
    DebugStreamPart,
    GraphOutput,           # invoke(version="v2") return type — .value, .interrupts
)
```
