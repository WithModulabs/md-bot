# Stream Filtering

Filter streaming output by node name, tag, or namespace.

## Contents

- Filter by Node Name
- Filter by Tag
- Filter by Namespace
- Combined Filters

## Filter by Node Name

Use `metadata["langgraph_node"]`:

```python
graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue
    msg, metadata = chunk["data"]

    # Only tokens from "model" node
    if msg.content and metadata.get("langgraph_node") == "model":
        print(msg.content, end="", flush=True)
```

In updates mode, filter by the node key:

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="updates", version="v2",
):
    for node, state in chunk["data"].items():
        if node == "analyzer":
            print(f"Analysis: {state}")
```

---

## Filter by Tag

Tag models during initialization, then filter:

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o", tags=["primary"])
```

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", version="v2",
):
    if chunk["type"] != "messages":
        continue
    msg, metadata = chunk["data"]
    if "primary" in metadata.get("tags", []):
        print(msg.content, end="", flush=True)
```

### Suppress Streaming with Built-in Tags

LangGraph provides built-in tags to control streaming behavior:

```python
from langgraph.constants import TAG_NOSTREAM, TAG_HIDDEN

# TAG_NOSTREAM ("nostream") — suppresses stream_mode="messages" for this model
# The model still runs, but tokens are not emitted to the message stream
background_model = init_chat_model("openai:gpt-4o-mini", tags=[TAG_NOSTREAM])

# TAG_HIDDEN ("langsmith:hidden") — hides the node from chain events entirely
# Use for internal processing nodes that shouldn't appear in streaming output
```

---

## Filter by Namespace

Separate root graph from subgraph/subagent events:

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue

    # Root only
    if not chunk["ns"]:
        handle_root(chunk)

    # Specific subgraph
    elif chunk["ns"][0].startswith("researcher"):
        handle_researcher(chunk)

    # Any subagent (tools: boundary in namespace)
    elif any(s.startswith("tools:") for s in chunk["ns"]):
        handle_subagent(chunk)
```

---

## Combined Filters

### Root Model Tokens + Subagent Status

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode=["messages", "updates"],
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "messages" and not chunk["ns"]:
        # Root graph tokens only
        msg, metadata = chunk["data"]
        if msg.content and metadata.get("langgraph_node") == "model":
            print(msg.content, end="", flush=True)

    elif chunk["type"] == "updates" and chunk["ns"]:
        # Subgraph/subagent state updates
        for node, state in chunk["data"].items():
            source = chunk["ns"][0].split(":")[0]
            print(f"\n[{source}/{node}] {list(state.keys())}")
```
