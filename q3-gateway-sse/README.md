
# Q3 — Inference API Gateway (SSE)

This folder contains a minimal Python gateway server that sits in front of an existing `/chat/completions` API and provides an enhanced **SSE** streaming experience:

**Gateway streaming order**
1. `prompt_summary`
2. `reasoning_summary`
3. `final_output_delta` (streamed)
4. `done`

It also includes:
- a small **client script** to call the gateway and print events
- a **mock upstream server** for local testing
- minimal **unit + integration tests**

---

## What problem this solves
Some reasoning-capable LLMs produce verbose intermediate reasoning content during streaming. This gateway:
- shows a **short summary** of the prompt first (fast TTFT),
- then shows a **summary of the model reasoning**,
- then streams the **final answer** to the user.

This improves end-user readability without breaking streaming UX.

---

## Assumptions (Reasoning detection)
The upstream stream does **not** explicitly label reasoning vs output tokens.

This implementation uses a simple heuristic:
- Reasoning content is detected as text **between markers**:
  - `REASONING_START` (default: `<think>`)
  - `REASONING_END` (default: `</think>`)
- If markers are missing, the gateway emits:
  - `reasoning_summary: "Reasoning not detected."`
---

## Project structure

```
q3_gateway_sse/
    server.py
    client.py
    mock_upstream.py
    requirements.txt
    tests/
        test_utils.py
        test_integration.py
```

## Setup

### Step 1

Install all the required dependencies
```bash
pip install -r requirements.txt
```

### Step 2

Start the upstream mock. This simulates a model server that streams

```bash
python -m uvicorn mock_upstream:app --host 127.0.0.1 --port 8001 --log-level info
```


### Step 3

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 9000 --log-level debug
```

### Step 4

Run the client end-to-end

```bash
python client.py --prompt "hi"
```

Expected output:

```bash
[prompt_summary] {'text': 'hi', 'ttft_ms': 0}
[reasoning_summary] {'text': 'I should greet in one sentence. Keep it short.'}
[final_output_delta] {'text': 'Hi! Nice to meet you.'}
[done] {}

--- FINAL OUTPUT ---
Hi! Nice to meet you.

```


### Tests

Use this command to run tests

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```


