import json
import os
import time
import httpx

from typing import Optional
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
REASONING_START = os.getenv("REASONING_START", "<think>")
REASONING_END = os.getenv("REASONING_END", "</think>")
MAX_REASONING_CHARS = int(os.getenv("MAX_REASONING_CHARS", "20000"))
MAX_BUFFERED_FINAL_CHARS = int(os.getenv("MAX_BUFFERED_FINAL_CHARS", "20000"))


def sse_event(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def extract_delta_content_from_upstream_line(line: str) -> Optional[str]:
    if not line.startswith("data:"):
        return None

    payload = line
    # Strip repeated 'data:' prefixes (because our mock wrapped SSE inside SSE)
    while payload.startswith("data:"):
        payload = payload[len("data:"):].lstrip()

    if payload == "[DONE]":
        return None

    try:
        obj = json.loads(payload)
        return obj["choices"][0]["delta"].get("content")
    except Exception:
        return None


def summarize_text(text: str, max_len: int = 220) -> str:
    t = " ".join(text.strip().split())
    if not t:
        return ""
    if len(t) > max_len:
        return t[: max_len - 3] + "..."
    return t


@app.get("/health")
def health():
    return {
        "ok": True,
        "upstream": UPSTREAM_BASE_URL,
        "reasoning_markers": [REASONING_START, REASONING_END],
    }


@app.post("/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()

    async def gen():
        t0 = time.time()

        msgs = body.get("messages", [])
        last_user = ""
        for m in reversed(msgs):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break

        yield sse_event(
            "prompt_summary",
            {
                "text": summarize_text(last_user, 200) or "No user message found.",
                "ttft_ms": int((time.time() - t0) * 1000),
            },
        )

        # Stream from upstream
        upstream_url = UPSTREAM_BASE_URL + "/chat/completions"

        in_reasoning = False
        reasoning_buf = ""
        final_buf = ""
        reasoning_summary_sent = False

        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", upstream_url, json={**body, "stream": True}) as r:
                    if r.status_code != 200:
                        yield sse_event("error", {"message": f"Upstream error {r.status_code}"})
                        yield sse_event("done", {})
                        return

                    async for line in r.aiter_lines():
                        if not line:
                            continue

                        chunk = extract_delta_content_from_upstream_line(line)
                        if chunk is None:
                            continue

                        # Reasoning boundaries
                        if REASONING_START in chunk:
                            in_reasoning = True
                            chunk = chunk.replace(REASONING_START, "")
                        if REASONING_END in chunk:
                            in_reasoning = False
                            chunk = chunk.replace(REASONING_END, "")

                            if not reasoning_summary_sent:
                                reasoning_summary_sent = True
                                yield sse_event(
                                    "reasoning_summary",
                                    {"text": summarize_text(reasoning_buf, 240) or "Reasoning not detected."},
                                )
                                if final_buf:
                                    yield sse_event("final_output_delta", {"text": final_buf})
                                    final_buf = ""

                        if in_reasoning and not reasoning_summary_sent:
                            if len(reasoning_buf) < MAX_REASONING_CHARS:
                                reasoning_buf += chunk
                            continue

                        if not reasoning_summary_sent:
                            if len(final_buf) < MAX_BUFFERED_FINAL_CHARS:
                                final_buf += chunk
                            continue

                        if chunk:
                            yield sse_event("final_output_delta", {"text": chunk})

            except httpx.HTTPError as e:
                yield sse_event("error", {"message": f"Upstream connection error: {str(e)}"})
                yield sse_event("done", {})
                return

        if not reasoning_summary_sent:
            yield sse_event(
                "reasoning_summary",
                {"text": summarize_text(reasoning_buf, 240) or "Reasoning not detected."},
            )
            if final_buf:
                yield sse_event("final_output_delta", {"text": final_buf})

        yield sse_event("done", {})

    return EventSourceResponse(gen())
