"""Simple chat UI powered by a local Ollama model and LangGraph."""

from typing import TypedDict, List

import gradio as gr
from langgraph.graph import END, StateGraph
from ollama import AsyncClient


class ChatState(TypedDict):
    messages: List[dict]


def build_workflow(model: str = "codellama"):
    client = AsyncClient()

    async def call_model(state: ChatState) -> ChatState:
        stream = await client.chat(model=model, messages=state["messages"], stream=True)
        reply = ""
        async for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            reply += content
        state["messages"].append({"role": "assistant", "content": reply})
        return state

    graph = StateGraph(ChatState)
    graph.add_node("model", call_model)
    graph.set_entry_point("model")
    graph.add_edge("model", END)
    return graph.compile()


workflow = build_workflow()


async def respond(message, history):
    messages: List[dict] = []
    for human, ai in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": ai})
    messages.append({"role": "user", "content": message})

    result = await workflow.ainvoke({"messages": messages})
    return result["messages"][-1]["content"]


demo = gr.ChatInterface(respond, title="Ollama LangGraph Chat")

if __name__ == "__main__":
    demo.launch()
