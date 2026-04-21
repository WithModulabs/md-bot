# Stream Modes

LangGraph v2 provides 7 stream modes. Pass as `stream_mode` to `stream()`/`astream()`.

## Contents

- All Modes
- Decision Framework

## All Modes

### `"messages"` — LLM Token Stream

Emits LLM tokens as `(message_chunk, metadata)` tuples. **Most commonly used.**

```python
from casts.oke.graph import oke_graph

graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    msg, metadata = chunk["data"]
    if msg.content:
        print(msg.content, end="", flush=True)
```

**Use when:** Displaying LLM output token-by-token in real time.

---

### `"updates"` — State Deltas

Emits only the **keys updated** by each node.

```python
async for chunk in graph.astream(inputs, config=config, stream_mode="updates", version="v2"):
    for node_name, updates in chunk["data"].items():
        print(f"{node_name} updated: {updates}")
```

**Use when:** Tracking which nodes ran and what they changed.

---

### `"custom"` — User-Defined Events

Emits data sent via `get_stream_writer()` from inside nodes.

```python
async for chunk in graph.astream(inputs, config=config, stream_mode="custom", version="v2"):
    print(f"Progress: {chunk['data']}")
```

**Use when:** Custom progress indicators, status updates, intermediate results.

---

### `"values"` — Full State Snapshots

Emits the **complete state** after each node execution.

```python
async for chunk in graph.astream(inputs, config=config, stream_mode="values", version="v2"):
    print(chunk["data"])  # {"query": "hello", "response": "..."}
```

**Use when:** State debugging, full state inspection at every step.

---

### `"tasks"` — Task Lifecycle

Emits task start/finish events with results and errors.

**Use when:** Monitoring node-level task execution lifecycle.

---

### `"checkpoints"` — Checkpoint Events

Emits checkpoint creation events. Requires a checkpointer on the graph.

**Use when:** Monitoring persistence state.

---

### `"debug"` — Full Debug Info

Combines checkpoints + tasks with extra metadata.

**Use when:** Maximum visibility during development.

---

## Decision Framework

```
What do you need to display?
├─ LLM tokens in real-time      → "messages"
├─ Node execution progress       → "updates"
├─ Custom progress bars/status   → "custom"
├─ Full state at every step      → "values"
├─ Task start/finish             → "tasks"
└─ Everything for debugging      → "debug"

Need multiple? → stream_mode=["messages", "updates", "custom"]
```

| Mode | Data Shape | Volume | Use Case |
|------|-----------|--------|----------|
| `messages` | `(token, metadata)` | High | Token-by-token display |
| `updates` | `{node: {keys...}}` | Medium | Execution tracking |
| `custom` | Any (user-defined) | Low-Medium | Progress events |
| `values` | Full state dict | High | State debugging |
| `tasks` | Task lifecycle | Low | Task monitoring |
| `checkpoints` | Checkpoint data | Low | Persistence monitoring |
| `debug` | Combined checkpoint+task | Medium | Full debugging |
