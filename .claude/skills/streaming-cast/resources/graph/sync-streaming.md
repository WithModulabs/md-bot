# Sync Streaming

Consume graph output synchronously using `graph.stream()`. Useful for scripts, CLI tools, and tests.

## Contents

- Basic Pattern
- Single Mode
- Multiple Modes

## Basic Pattern

```python
from casts.oke.graph import oke_graph

graph = oke_graph()

config = {"configurable": {"thread_id": "session-1"}}

for chunk in graph.stream(
    {"messages": [HumanMessage(content="hello")]},
    config=config,
    stream_mode="messages",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content:
            print(msg.content, end="", flush=True)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | dict \| Command \| None | — | Input state |
| `config` | dict \| None | `None` | Execution config (thread_id, actor_id, etc.) |
| `stream_mode` | str \| list | graph default | Which mode(s) to stream |
| `print_mode` | str \| list | `()` | Same as stream_mode, but only prints to console for debugging. Does not affect stream output |
| `subgraphs` | bool | `False` | Include subgraph/subagent outputs |
| `version` | `"v1"` \| `"v2"` | `"v1"` | Always use `"v2"` for typed StreamPart output |
| `output_keys` | str \| list \| None | `None` | Limit which state keys are streamed |
| `interrupt_before` | list \| `"*"` \| None | `None` | Nodes to interrupt before execution |
| `interrupt_after` | list \| `"*"` \| None | `None` | Nodes to interrupt after execution |
| `context` | ContextT \| None | `None` | Static context for the run (v0.6.0+) |
| `durability` | `"sync"` \| `"async"` \| `"exit"` \| None | `None` | Checkpoint persistence timing. Requires checkpointer |

---

## Single Mode

```python
graph = oke_graph()

# Messages — token-by-token
for chunk in graph.stream(inputs, config=config, stream_mode="messages", version="v2"):
    msg, metadata = chunk["data"]
    if msg.content:
        print(msg.content, end="", flush=True)

# Updates — node execution tracking
for chunk in graph.stream(inputs, config=config, stream_mode="updates", version="v2"):
    for node, updates in chunk["data"].items():
        print(f"{node}: {updates}")

# Custom — progress events
for chunk in graph.stream(inputs, config=config, stream_mode="custom", version="v2"):
    print(f"Event: {chunk['data']}")
```

---

## Multiple Modes

```python
graph = oke_graph()

for chunk in graph.stream(
    inputs, config=config,
    stream_mode=["messages", "updates", "custom"],
    version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content:
            print(msg.content, end="", flush=True)

    elif chunk["type"] == "updates":
        for node, state in chunk["data"].items():
            print(f"\n[{node}] updated")

    elif chunk["type"] == "custom":
        print(f"\nStatus: {chunk['data']}")
```
