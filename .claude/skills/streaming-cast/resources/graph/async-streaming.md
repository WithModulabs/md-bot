# Async Streaming

Consume graph output asynchronously using `graph.astream()`. Used in runtime endpoints and API handlers.

## Contents

- Basic Pattern
- With Config
- Python < 3.11 Workaround
- Parallel Streaming

## Basic Pattern

```python
from casts.oke.graph import oke_graph

graph = oke_graph()

config = {"configurable": {"thread_id": "session-1"}}

async for chunk in graph.astream(
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

---

## With Config

Pass `config` with `configurable` for thread/actor scoping:

```python
graph = oke_graph()

config = {
    "configurable": {
        "actor_id": user_id,
        "thread_id": session_id,
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
    # ... dispatch to transport
```

---

## print_mode (Debug Output)

`print_mode` accepts the same values as `stream_mode`, but only prints to console — does not affect the stream output. Useful for debugging without modifying consumer code:

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages",
    print_mode=["updates", "values"],  # prints to console only
    subgraphs=True,
    version="v2",
):
    # chunk only contains "messages" events
    # "updates" and "values" are printed to console for debugging
    ...
```

Also automatically enabled when `debug=True` (prints `["updates", "values"]`).

---

## Python < 3.11 Workaround

Python < 3.11 asyncio doesn't propagate context automatically. Pass `config` explicitly to `astream()` **and** to LLM calls inside async nodes:

```python
from casts.base_node import AsyncBaseNode

class LLMNode(AsyncBaseNode):
    async def execute(self, state, config):
        # Explicit config propagation ensures streaming callbacks work
        response = await self.model.ainvoke(state["messages"], config)
        return {"response": response}
```

**Recommendation:** Upgrade to Python 3.11+.

---

## Parallel Streaming

Stream from multiple graphs concurrently:

```python
import asyncio
from casts.oke.graph import oke_graph
from casts.another_cast.graph import another_cast_graph

async def stream_both(inputs, config):
    async def consume(graph, name):
        async for chunk in graph.astream(
            inputs, config=config,
            stream_mode="messages", subgraphs=True, version="v2",
        ):
            if chunk["type"] == "messages":
                msg, _ = chunk["data"]
                if msg.content:
                    print(f"[{name}] {msg.content}", end="")

    await asyncio.gather(
        consume(oke_graph(), "oke"),
        consume(another_cast_graph(), "another_cast"),
    )
```
