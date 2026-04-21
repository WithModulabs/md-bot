---
name: streaming-cast
description: Implements LangGraph v2 streaming for graphs with subgraphs and agents. Use when adding streaming to runtime/API endpoint, need token streaming, custom stream events, namespace parsing, or ask "add streaming", "stream tokens", "stream graph".
version: "2026.04.01"
author: Proact0
allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion
---
# Streaming Md Bot's Casts (v2)

Implement v2 streaming to consume `oke_graph()` output in runtime, API endpoints, or other consumers.

## When to Use

- Adding streaming output to a runtime or API endpoint
- Need token-by-token LLM output, tool call, tool result streaming
- Custom progress events from nodes via stream writer
- Namespace parsing for subgraph/subagent source identification
- Transport integration (SSE recommended, WebSocket optional)

## When NOT to Use

- Building graph structure (nodes, edges, state) → `developing-cast`
- DeepAgent harness (create_deep_agent, backends) → `developing-deepagent`
- Architecture design → `architecting-act`
- Testing → `testing-cast`

---

## Quick Start

```python
from langchain_core.messages import HumanMessage

from casts.oke.graph import oke_graph

graph = oke_graph()

config = {
    "configurable": {
        "actor_id": "user-123",
        "thread_id": "session-1",
    },
    "recursion_limit": 2000,
}

async for chunk in graph.astream(
    {"messages": [HumanMessage(content="hello")]},
    config=config,
    stream_mode="messages",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        # node == "model" for agent graphs, adjust for custom graphs
        if msg.content and metadata.get("langgraph_node") == "model":
            print(msg.content, end="", flush=True)
```

---

## Implementation Workflow

### Step 1: Choose Stream Mode(s)

See [core/stream-modes.md](./resources/core/stream-modes.md).

| Goal | Stream Mode |
|------|------------|
| LLM token-by-token output | `"messages"` |
| Track node execution steps | `"updates"` |
| Custom progress events | `"custom"` |
| Full state after each step | `"values"` |

Combine: `stream_mode=["messages", "updates", "custom"]`

### Step 2: Consume the Stream

Import the graph, call it, iterate with `stream()`/`astream()`.

```python
graph = oke_graph()
async for chunk in graph.astream(inputs, config, stream_mode=..., subgraphs=True, version="v2"):
    ...
```

### Step 3: Handle Message Types

Dispatch based on message properties:
- Token → `msg.content` with `node == "model"`
- Tool call → `msg.tool_call_chunks`
- Tool result → `msg.type == "tool"`

See [graph/message-handling.md](./resources/graph/message-handling.md).

### Step 4: Parse Namespace (if subgraphs/subagents)

Use `chunk["ns"]` to identify event source.

See [subgraph/nested-streaming.md](./resources/subgraph/nested-streaming.md).

### Step 5: Wire to Transport (SSE or WebSocket)

See [patterns/integration.md](./resources/patterns/integration.md). SSE is the LangChain ecosystem recommended transport.

---

## Component Reference

### Core Concepts

| Use when | Resource |
|----------|----------|
| choosing which stream mode(s) to use | [core/stream-modes.md](./resources/core/stream-modes.md) |
| understanding StreamPart format and type narrowing | [core/streampart-format.md](./resources/core/streampart-format.md) |
| emitting custom events from nodes (get_stream_writer) | [core/stream-writer.md](./resources/core/stream-writer.md) |

### Stream Consumption

| Use when | Resource |
|----------|----------|
| sync streaming (scripts, tests) | [graph/sync-streaming.md](./resources/graph/sync-streaming.md) |
| async streaming (runtime, API endpoints) | [graph/async-streaming.md](./resources/graph/async-streaming.md) |
| handling tokens, tool calls, tool results | [graph/message-handling.md](./resources/graph/message-handling.md) |

### Subgraph & Namespace

| Use when | Resource |
|----------|----------|
| streaming through subgraphs (subgraphs=True) | [subgraph/subgraph-streaming.md](./resources/subgraph/subgraph-streaming.md) |
| parsing multi-level namespaces (_parse_source) | [subgraph/nested-streaming.md](./resources/subgraph/nested-streaming.md) |
| streaming create_agent/create_deep_agent (node or subgraph) | [subgraph/agent-streaming.md](./resources/subgraph/agent-streaming.md) |

### Patterns

| Use when | Resource |
|----------|----------|
| filtering by node name, tag, or namespace | [patterns/filtering.md](./resources/patterns/filtering.md) |
| combining multiple stream modes | [patterns/multiple-modes.md](./resources/patterns/multiple-modes.md) |
| SSE / WebSocket transport integration | [patterns/integration.md](./resources/patterns/integration.md) |

---

## Verification

- [ ] Stream mode(s) chosen for use case
- [ ] `version="v2"` passed to all `stream()`/`astream()` calls
- [ ] `subgraphs=True` set when graph has internal subgraphs/subagents
- [ ] Message types handled (token, tool_call, tool_result, done)
- [ ] Namespace parsed correctly for source identification
- [ ] Agent/DeepAgent streaming verified (subgraphs=True propagates through agents)
- [ ] Transport layer tested end-to-end (SSE / WebSocket)
