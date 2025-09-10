"""Simple chat UI powered by a local Ollama model.

Requires an Ollama server (`ollama serve`) running and a model pulled
locally. Configure the host and model via the `OLLAMA_HOST` and
`OLLAMA_MODEL` environment variables.
"""

import asyncio
import os
from typing import List

import gradio as gr
from ollama import AsyncClient

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama")

client = AsyncClient(host=OLLAMA_HOST)


async def respond(message, history):
    messages: List[dict] = []
    for human, ai in history:
        messages.append({"role": "user", "content": human})
        messages.append({"role": "assistant", "content": ai})
    messages.append({"role": "user", "content": message})

    stream = await client.chat(model=OLLAMA_MODEL, messages=messages, stream=True)
    reply = ""
    async for chunk in stream:
        reply += chunk.get("message", {}).get("content", "")
    return reply


async def ensure_server():
    try:
        await client.list()
    except Exception as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"Could not connect to Ollama server at {OLLAMA_HOST}. Make sure it is running.") from exc


if __name__ == "__main__":
    asyncio.run(ensure_server())
    gr.ChatInterface(respond, title="Ollama Chat").launch()
