# Agent & DeepAgent Streaming

Stream through `create_agent` and `create_deep_agent` that run as subgraphs within a parent graph.

## Contents

- Graph Topology Patterns
- create_agent as Node Subgraph
- create_agent Inside a Node
- create_deep_agent as Node Subgraph
- create_deep_agent Inside a Node
- create_deep_agent with Subagents (as Node Subgraph)
- create_deep_agent with Subagents (Inside a Node)
- Namespace Structure by Pattern

## Graph Topology Patterns

Agents compiled by `create_agent` and `create_deep_agent` are `CompiledStateGraph` instances — they are subgraphs. When added to a parent graph, `subgraphs=True` automatically streams their internal events.

```
Pattern 1: graph → create_agent (node = subgraph)
Pattern 2: graph → node containing create_agent (node invokes subgraph internally)
Pattern 3: graph → create_deep_agent (node = subgraph)
Pattern 4: graph → node containing create_deep_agent (node invokes subgraph internally)
Pattern 5: graph → create_deep_agent → subagent (nested subgraph)
Pattern 6: graph → node containing create_deep_agent → subagent (nested subgraph)
```

---

## create_agent as Node Subgraph

When `create_agent` is added directly as a node, it runs as a subgraph. Its internal `model` and `tools` nodes emit streaming events automatically.

```python
# casts/{cast_name}/graph.py
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from casts.base_graph import BaseGraph

class AgentGraph(BaseGraph):
    def build(self):
        agent = create_agent(
            model="anthropic:claude-sonnet-4-5-20250929",
            tools=[search_tool],
        )

        builder = StateGraph(State)
        builder.add_node("preprocess", PreprocessNode())
        builder.add_node("agent", agent)  # subgraph node
        builder.add_node("postprocess", PostprocessNode())

        builder.add_edge(START, "preprocess")
        builder.add_edge("preprocess", "agent")
        builder.add_edge("agent", "postprocess")
        builder.add_edge("postprocess", END)

        graph = builder.compile()
        graph.name = self.name
        return graph
```

Stream consumption:

```python
graph = agent_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue

    msg, metadata = chunk["data"]
    node = metadata.get("langgraph_node")

    # Agent's internal model node emits tokens
    # ns: ("agent:<task_id>",) for the subgraph
    # node: "model" for the LLM call inside create_agent
    if msg.content and node == "model":
        print(f"[{_parse_source(chunk['ns'])}] {msg.content}", end="")
```

---

## create_agent Inside a Node

When a node internally invokes a `create_agent` graph, the agent runs as a nested subgraph. Streaming works the same way — the parent node wraps the agent call.

```python
# casts/{cast_name}/modules/nodes.py
from casts.base_node import AsyncBaseNode
from .agents import set_sample_agent

class AgentNode(AsyncBaseNode):
    def __init__(self):
        super().__init__()
        self.agent = set_sample_agent()

    async def execute(self, state, config):
        # invoke propagates streaming context automatically
        result = await self.agent.ainvoke(
            {"messages": state["messages"]}, config
        )
        return {"messages": result["messages"]}
```

> **Key:** Pass `config` to `ainvoke()` so the streaming callback chain propagates. Without config propagation, `stream_mode="messages"` won't capture inner LLM tokens.

```python
# casts/{cast_name}/graph.py
builder.add_node("agent_node", AgentNode())  # node wrapping agent
```

Stream consumption is identical — the namespace reflects the nesting:

```python
# ns: ("agent_node:<task_id>",) for the wrapping node
# The agent's internal LLM calls are captured via callback propagation
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content and metadata.get("langgraph_node") == "model":
            print(msg.content, end="")
```

---

## create_deep_agent as Node Subgraph

`create_deep_agent` returns a `CompiledStateGraph`. Add it as a node for automatic subgraph streaming:

```python
# casts/{cast_name}/graph.py
from deepagents import create_deep_agent

class DeepAgentGraph(BaseGraph):
    def build(self):
        deep_agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-5-20250929",
            tools=[search_tool],
            system_prompt="You are a research assistant.",
        )

        builder = StateGraph(State)
        builder.add_node("deep_agent", deep_agent)  # subgraph node
        builder.add_edge(START, "deep_agent")
        builder.add_edge("deep_agent", END)

        graph = builder.compile()
        graph.name = self.name
        return graph
```

Stream consumption:

```python
graph = deep_agent_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue

    msg, metadata = chunk["data"]
    source = _parse_source(chunk["ns"])
    node = metadata.get("langgraph_node")

    # deep_agent's internal model node
    if msg.content and node == "model":
        print(f"[{source}] {msg.content}", end="")
```

---

## create_deep_agent Inside a Node

When a node internally invokes a `create_deep_agent` graph, streaming works the same way as `create_agent` inside a node — pass `config` to propagate the streaming callback chain.

```python
# casts/{cast_name}/modules/nodes.py
from casts.base_node import AsyncBaseNode
from .agents import set_deep_agent

class DeepAgentNode(AsyncBaseNode):
    def __init__(self):
        super().__init__()
        self.agent = set_deep_agent()

    async def execute(self, state, config):
        # config propagation is critical for streaming
        result = await self.agent.ainvoke(
            {"messages": state["messages"]}, config
        )
        return {"messages": result["messages"]}
```

> **Key:** Pass `config` to `ainvoke()` so the streaming callback chain propagates. Without config propagation, `stream_mode="messages"` won't capture inner LLM tokens.

```python
# casts/{cast_name}/graph.py
builder.add_node("deep_agent_node", DeepAgentNode())  # node wrapping deep_agent
```

Stream consumption is identical — the namespace reflects the wrapping node:

```python
# ns: ("deep_agent_node:<task_id>",) for the wrapping node
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content and metadata.get("langgraph_node") == "model":
            print(msg.content, end="")
```

---

## create_deep_agent with Subagents (as Node Subgraph)

When `create_deep_agent` has subagents, they run as nested subgraphs within the deep agent. The namespace grows deeper:

```
graph → deep_agent → subagent
                 ns: ("deep_agent:<id>", "tools:<id>", "researcher:<id>")
```

```python
# casts/{cast_name}/graph.py
from deepagents import create_deep_agent

class OrchestratorGraph(BaseGraph):
    def build(self):
        deep_agent = create_deep_agent(
            model="anthropic:claude-sonnet-4-5-20250929",
            tools=[search_tool],
            subagents=[
                {
                    "name": "researcher",
                    "description": "Research specialist",
                    "system_prompt": "You are a researcher.",
                    "tools": [web_search],
                },
                {
                    "name": "writer",
                    "description": "Report writer",
                    "system_prompt": "You write reports.",
                    "tools": [],
                },
            ],
        )

        builder = StateGraph(State)
        builder.add_node("orchestrator", deep_agent)
        builder.add_edge(START, "orchestrator")
        builder.add_edge("orchestrator", END)

        graph = builder.compile()
        graph.name = self.name
        return graph
```

Stream with subagent source separation:

```python
graph = orchestrator_graph()

async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] != "messages":
        continue

    msg, metadata = chunk["data"]
    source = _parse_source(chunk["ns"])
    node = metadata.get("langgraph_node")

    if msg.content and node == "model":
        # source identifies: "oke" (main), "researcher", "writer"
        print(f"[{source}] {msg.content}", end="")
```

---

## create_deep_agent with Subagents (Inside a Node)

When a node internally invokes a `create_deep_agent` that has subagents, the streaming behavior combines Pattern 4 and Pattern 5. The wrapping node's namespace replaces the direct subgraph namespace.

```python
# casts/{cast_name}/modules/nodes.py
from casts.base_node import AsyncBaseNode
from .agents import set_orchestrator_agent

class OrchestratorNode(AsyncBaseNode):
    def __init__(self):
        super().__init__()
        self.agent = set_orchestrator_agent()  # create_deep_agent with subagents

    async def execute(self, state, config):
        result = await self.agent.ainvoke(
            {"messages": state["messages"]}, config
        )
        return {"messages": result["messages"]}
```

```python
# casts/{cast_name}/graph.py
builder.add_node("orchestrator_node", OrchestratorNode())
```

Stream consumption:

```python
async for chunk in graph.astream(
    inputs, config=config,
    stream_mode="messages", subgraphs=True, version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        source = _parse_source(chunk["ns"])
        if msg.content and metadata.get("langgraph_node") == "model":
            # source: "oke" (main), "researcher", "writer"
            print(f"[{source}] {msg.content}", end="")
```

---

## Namespace Structure by Pattern

| Pattern | `ns` value | `_parse_source` result |
|---------|-----------|----------------------|
| graph (root) | `()` | `"oke"` |
| graph → create_agent | `("agent:<id>",)` | `"oke"` |
| graph → create_agent → tool | `("agent:<id>", "tools:<id>")` | `"oke"` |
| graph → node(create_agent) | `("agent_node:<id>",)` | `"oke"` |
| graph → create_deep_agent | `("deep_agent:<id>",)` | `"oke"` |
| graph → node(create_deep_agent) | `("deep_agent_node:<id>",)` | `"oke"` |
| graph → deep_agent → tool | `("deep_agent:<id>", "tools:<id>")` | `"oke"` |
| graph → deep_agent → subagent | `("deep_agent:<id>", "tools:<id>", "researcher:<id>")` | `"researcher"` |
| graph → deep_agent → subagent → tool | `("deep_agent:<id>", "tools:<id>", "researcher:<id>", "tools:<id2>")` | `"researcher"` |
| graph → node(deep_agent) → subagent | `("orchestrator_node:<id>", "tools:<id>", "researcher:<id>")` | `"researcher"` |
| graph → node(deep_agent) → subagent → tool | `("orchestrator_node:<id>", "tools:<id>", "researcher:<id>", "tools:<id2>")` | `"researcher"` |
