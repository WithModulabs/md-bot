# Custom Stream Writer

Emit custom streaming events from inside nodes using `get_stream_writer()`.

## Contents

- Sync Nodes
- Async Nodes (Python 3.11+)
- Async Nodes (Python < 3.11)
- With BaseNode (runtime parameter)
- Progress Patterns

## Sync Nodes

```python
from langgraph.config import get_stream_writer

def process_data(state):
    writer = get_stream_writer()

    writer({"status": "starting", "step": 1})
    # ... do work ...
    writer({"status": "processing", "progress": 50})
    # ... more work ...
    writer({"status": "complete", "progress": 100})

    return {"result": "done"}
```

Consumer receives these with `stream_mode="custom"`:

```python
graph = oke_graph()

for chunk in graph.stream(inputs, stream_mode="custom", version="v2"):
    print(chunk["data"])
    # {"status": "starting", "step": 1}
    # {"status": "processing", "progress": 50}
    # {"status": "complete", "progress": 100}
```

---

## Async Nodes (Python 3.11+)

```python
from langgraph.config import get_stream_writer

async def async_process(state):
    writer = get_stream_writer()
    writer({"status": "running"})
    result = await fetch_data()
    writer({"status": "done"})
    return {"data": result}
```

---

## Async Nodes (Python < 3.11)

`get_stream_writer()` is unavailable in async contexts. Use `StreamWriter` parameter injection:

```python
from langgraph.types import StreamWriter

async def async_process(state, writer: StreamWriter):
    # LangGraph injects writer automatically when declared as parameter
    writer({"status": "running"})
    result = await fetch_data()
    writer({"status": "done"})
    return {"data": result}
```

---

## With BaseNode (runtime parameter)

Access the stream writer via the `runtime` parameter:

```python
from casts.base_node import BaseNode

class ProcessNode(BaseNode):
    def execute(self, state, runtime):
        writer = runtime.stream_writer
        writer({"status": "processing", "node": self.name})
        # ... do work ...
        writer({"status": "complete", "node": self.name})
        return {"result": "done"}
```

Async:

```python
from casts.base_node import AsyncBaseNode

class AsyncProcessNode(AsyncBaseNode):
    async def execute(self, state, runtime):
        writer = runtime.stream_writer
        writer({"status": "processing", "node": self.name})
        result = await self.fetch()
        writer({"status": "complete", "node": self.name})
        return {"data": result}
```

---

## Progress Patterns

### Percentage Progress

```python
class BatchProcessNode(BaseNode):
    def execute(self, state, runtime):
        writer = runtime.stream_writer
        items = state["items"]

        for i, item in enumerate(items):
            progress = int((i + 1) / len(items) * 100)
            writer({"progress": progress, "current": item})
            self.process_item(item)

        return {"processed": len(items)}
```

### Streaming Non-LangChain Model Output

```python
from langgraph.config import get_stream_writer

async def stream_external_llm(state):
    writer = get_stream_writer()
    response = ""

    async for chunk in external_model.stream(state["prompt"]):
        response += chunk.text
        writer({"token": chunk.text, "role": "assistant"})

    return {"response": response}
```
