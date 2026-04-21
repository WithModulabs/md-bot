# Multiple Stream Modes

Combine stream modes for comprehensive event coverage.

## Contents

- Combining Modes
- Common Combinations
- Dispatch Pattern
- Performance

## Combining Modes

Pass a list to `stream_mode`:

```python
graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=["messages", "updates", "custom"],
    subgraphs=True,
    version="v2",
):
    # All chunks share the same StreamPart format
    # Differentiate by chunk["type"]
    print(f"[{chunk['type']}] {chunk['data']}")
```

---

## Common Combinations

### Messages + Updates (Most Common)

Token streaming + node execution tracking:

```python
stream_mode = ["messages", "updates"]

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=stream_mode, subgraphs=True, version="v2",
):
    if chunk["type"] == "updates":
        for node, state in chunk["data"].items():
            print(f"\n--- {node} ---")
    elif chunk["type"] == "messages":
        msg, _ = chunk["data"]
        if msg.content:
            print(msg.content, end="", flush=True)
```

### Messages + Custom (Progress + Tokens)

Token streaming + custom progress events:

```python
stream_mode = ["messages", "custom"]

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=stream_mode, subgraphs=True, version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content and metadata.get("langgraph_node") == "model":
            print(msg.content, end="", flush=True)
    elif chunk["type"] == "custom":
        if "progress" in chunk["data"]:
            print(f"\nProgress: {chunk['data']['progress']}%")
```

### Messages + Updates + Custom (Full Visibility)

Everything — recommended for debugging and monitoring:

```python
stream_mode = ["messages", "updates", "custom"]

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=stream_mode, subgraphs=True, version="v2",
):
    source = _parse_source(chunk["ns"])

    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content and metadata.get("langgraph_node") == "model":
            print(f"[{source}] {msg.content}", end="")

    elif chunk["type"] == "updates":
        for node, state in chunk["data"].items():
            print(f"[{source}/{node}] {list(state.keys())}")

    elif chunk["type"] == "custom":
        print(f"[{source}] custom: {chunk['data']}")
```

---

## Dispatch Pattern

Clean handler dispatch for multi-mode streams:

```python
def handle_messages(data, ns):
    msg, metadata = data
    if msg.content and metadata.get("langgraph_node") == "model":
        print(msg.content, end="", flush=True)

def handle_updates(data, ns):
    for node, state in data.items():
        print(f"[{node}] {state}")

def handle_custom(data, ns):
    print(f"Event: {data}")

HANDLERS = {
    "messages": handle_messages,
    "updates": handle_updates,
    "custom": handle_custom,
}

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=["messages", "updates", "custom"],
    subgraphs=True, version="v2",
):
    handler = HANDLERS.get(chunk["type"])
    if handler:
        handler(chunk["data"], chunk["ns"])
```

---

## Performance

| Modes | Volume | Use Case |
|-------|--------|----------|
| `["messages"]` | High | Token display (production) |
| `["messages", "updates"]` | Medium-High | Interactive UI |
| `["messages", "custom"]` | Medium-High | Progress + tokens |
| `["messages", "updates", "custom"]` | High | Full monitoring |
| `["updates"]` | Low | Backend monitoring |
