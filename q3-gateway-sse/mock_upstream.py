import asyncio
import json
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse

app = FastAPI()


def _wrap_openai_delta(text: str) -> str:
    obj = {"choices": [{"delta": {"content": text}}]}
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


@app.post("/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    if not body.get("stream", False):
        return {"error": "mock upstream supports only stream=true"}

    mode = body.get("mode", "normal")

    if mode == "normal":
        chunks = [
            "<think>",
            "I should greet in one sentence. ",
            "Keep it short. ",
            "</think>",
            "Hi! Nice to meet you.",
        ]
    elif mode == "no_reasoning":
        chunks = [
            "Hi! Nice to meet you.",
        ]
    elif mode == "split_markers":
        chunks = [
            "<thi",
            "nk>",
            "I should greet in one sentence. ",
            "Keep it short. ",
            "</th",
            "ink>",
            "Hi! Nice to meet you.",
        ]
    else:
        return {"error": f"unknown mode: {mode}"}

    async def gen():
        for c in chunks:
            yield {"event": "message", "data": _wrap_openai_delta(c)}
            await asyncio.sleep(0.15)

        yield {"event": "message", "data": "data: [DONE]\n\n"}

    return EventSourceResponse(gen())
