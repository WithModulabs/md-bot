# Transport Integration

Stream graph events to external consumers via SSE or WebSocket.

## Contents

- SSE (Recommended)
- WebSocket
- SSE Protocol

## SSE (Recommended)

Server-Sent Events — LangChain/LangGraph ecosystem recommended pattern for HTTP-based streaming:

```python
import json
import logging

from langchain_core.messages import AIMessageChunk, HumanMessage

from casts.oke.graph import oke_graph

logger = logging.getLogger(__name__)


def _parse_source(ns: tuple[str, ...]) -> str:
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


async def event_generator(query: str, config: dict):
    """SSE event generator. Framework-agnostic async generator."""
    graph = oke_graph()
    inputs = {"messages": [HumanMessage(content=query)]}

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

        if msg.content and node == "model":
            yield f"event: token\ndata: {json.dumps({'content': msg.content, 'source': source})}\n\n"

        if isinstance(msg, AIMessageChunk) and msg.tool_call_chunks:
            for tc in msg.tool_call_chunks:
                if tc.get("name"):
                    yield f"event: tool_call\ndata: {json.dumps({'name': tc['name'], 'source': source})}\n\n"

        if msg.type == "tool":
            yield f"event: tool_result\ndata: {json.dumps({'name': msg.name, 'content': str(msg.content), 'source': source})}\n\n"

    yield "event: done\ndata: {}\n\n"
```

The `event_generator` is a plain async generator — integrate with any Python web framework (FastAPI, Starlette, aiohttp, Django Channels, etc.) by wiring it to an SSE response.

---

## WebSocket

WebSocket pattern — use when bidirectional communication or real-time push is required:

```python
import logging

from langchain_core.messages import AIMessageChunk, HumanMessage

from casts.oke.graph import oke_graph

logger = logging.getLogger(__name__)


def _parse_source(ns: tuple[str, ...]) -> str:
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


async def handle_websocket_message(send_json, data: dict) -> None:
    """Handle a single WebSocket message. Framework-agnostic.

    Args:
        send_json: Callable that sends a JSON-serializable dict to the client.
        data: Parsed JSON message from the client.
    """
    graph = oke_graph()
    inputs = {
        "messages": [HumanMessage(content=data.get("query", ""))],
    }
    config = {
        "configurable": {
            "actor_id": data.get("user_id", "anonymous"),
            "thread_id": data.get("session_id", "default"),
        },
        "recursion_limit": 2000,
    }

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

        if msg.content and node == "model":
            await send_json(
                {"type": "token", "content": msg.content, "source": source}
            )

        if isinstance(msg, AIMessageChunk) and msg.tool_call_chunks:
            for tc in msg.tool_call_chunks:
                if tc.get("name"):
                    await send_json({
                        "type": "tool_call",
                        "name": tc["name"],
                        "args": tc.get("args", ""),
                        "id": tc.get("id", ""),
                        "source": source,
                    })

        if msg.type == "tool":
            await send_json({
                "type": "tool_result",
                "name": msg.name,
                "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                "tool_call_id": msg.tool_call_id,
                "source": source,
            })

    await send_json({"type": "done"})
```

---

## SSE Protocol

| Direction | Event | Data |
|-----------|-------|------|
| S→C | `token` | `{content, source}` |
| S→C | `tool_call` | `{name, source}` |
| S→C | `tool_result` | `{name, content, source}` |
| S→C | `done` | `{}` |