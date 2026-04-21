# Message Handling

Handle LLM tokens, tool calls, and tool results from `stream_mode="messages"`.

## Contents

- Message Types
- Token Handling
- Tool Call Handling
- Tool Result Handling
- Complete Dispatch Pattern
- Detect Message Completion
- Reasoning/Thinking Tokens

## Message Types

With `stream_mode="messages"`, each chunk's data is a `(message_chunk, metadata)` tuple:

| `msg` type | Property | Description |
|------------|----------|-------------|
| `AIMessageChunk` | `msg.content` | LLM text token |
| `AIMessageChunk` | `msg.tool_call_chunks` | LLM decided to call a tool |
| Tool message | `msg.type == "tool"` | Tool execution result |

---

## Token Handling

> **Note:** `metadata["langgraph_node"]` returns the node name registered with `add_node()`.
> For agent-based graphs (`create_agent`, `create_deep_agent`), the LLM node is named `"model"`.
> For custom StateGraph, it matches your `add_node("YourNodeName", ...)` call.

```python
from langchain_core.messages import AIMessageChunk

graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue

    msg, metadata = chunk["data"]
    node = metadata.get("langgraph_node")

    # Text tokens — filter by node name
    # Agent graphs: node == "model"
    # Custom graphs: node == "YourNodeName"
    if msg.content and node == "model":
        await send_token(msg.content)
```

---

## Tool Call Handling

When the model decides to call a tool, it emits `AIMessageChunk` with `tool_call_chunks`:

```python
    if isinstance(msg, AIMessageChunk) and msg.tool_call_chunks:
        for tc in msg.tool_call_chunks:
            if tc.get("name"):
                await send_tool_call(
                    name=tc["name"],
                    args=tc.get("args", ""),
                    id=tc.get("id", ""),
                )
```

---

## Tool Result Handling

After tool execution, the result comes back as a tool message:

```python
    if msg.type == "tool":
        await send_tool_result(
            name=msg.name,
            content=msg.content if isinstance(msg.content, str) else str(msg.content),
            tool_call_id=msg.tool_call_id,
        )
```

---

## Complete Dispatch Pattern

Full message dispatch as used in runtime endpoints. `send` is any async callable that delivers a dict to the client (SSE yield, WebSocket send, etc.):

```python
from langchain_core.messages import AIMessageChunk

graph = oke_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] != "messages":
        continue

    msg, metadata = chunk["data"]
    source = _parse_source(chunk["ns"])
    node = metadata.get("langgraph_node")

    # 1. Text tokens (node == "model" for agent graphs, adjust for custom graphs)
    if msg.content and node == "model":
        await send({"type": "token", "content": msg.content, "source": source})

    # 2. Tool calls
    if isinstance(msg, AIMessageChunk) and msg.tool_call_chunks:
        for tc in msg.tool_call_chunks:
            if tc.get("name"):
                await send({
                    "type": "tool_call",
                    "name": tc["name"],
                    "args": tc.get("args", ""),
                    "id": tc.get("id", ""),
                    "source": source,
                })

    # 3. Tool results
    if msg.type == "tool":
        await send({
            "type": "tool_result",
            "name": msg.name,
            "content": msg.content if isinstance(msg.content, str) else str(msg.content),
            "tool_call_id": msg.tool_call_id,
            "source": source,
        })

# 4. Done
await send({"type": "done"})
```

---

## Detect Message Completion

Use `chunk_position` metadata:

```python
buffer = ""

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", version="v2",
):
    if chunk["type"] != "messages":
        continue
    msg, metadata = chunk["data"]

    if msg.content:
        buffer += msg.content

    if metadata.get("chunk_position") == "last":
        process_complete_message(buffer)
        buffer = ""
```

---

## Reasoning/Thinking Tokens

For models with extended thinking (e.g., Claude):

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", version="v2",
):
    if chunk["type"] != "messages":
        continue
    msg, metadata = chunk["data"]

    if hasattr(msg, "content_blocks") and msg.content_blocks:
        for block in msg.content_blocks:
            if block["type"] == "reasoning":
                pass  # thinking token — hide or show separately
            elif block["type"] == "text":
                print(block.get("text", ""), end="", flush=True)
    elif msg.content:
        print(msg.content, end="", flush=True)
```
