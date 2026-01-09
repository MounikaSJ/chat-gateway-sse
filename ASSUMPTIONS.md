# Assumptions / Constraints introduced

## Q2(a) — Broken model fix (chat completions)
- **Chat template content choice:** The original model repo did not include `tokenizer_config.json: chat_template`. Added a **ChatML-style** `chat_template` that matches the model’s special tokens (e.g., `<|im_start|>`, `<|im_end|>`). This template was selected as a practical default for OpenAI-style `/chat/completions` behavior.

## Q3 — Gateway SSE (prompt summary + reasoning summary + final output)
- **Reasoning delimiters:** Assumed “reasoning” is delimited by configurable marker strings (defaulting to `<think>` and `</think>`), provided via `.env` (`REASONING_START`, `REASONING_END`).

- **Summary method:** Assumed the “summary” is in the format such as trim whitespace + cap length rather than an LLM-generated summary. This keeps the gateway fast and dependency-free.

- **Upstream streaming format:** Assumed the upstream produces JSON chunks (e.g., `{"choices":[{"delta":{"content":"..."}}]}`) and signals completion with `[DONE]`.

- **Event schema:** Assumed a specific SSE event schema and ordering:
  - `prompt_summary` emitted first
  - `reasoning_summary` emitted before any final output
  - `final_output_delta` streamed after `reasoning_summary`
  - `done` emitted last

- **Buffering policy:** Assumed it is acceptable to **buffer final output** until reasoning ends to guarantee `reasoning_summary` arrives before `final_output_delta`.

- **Safety caps:** Introduced caps to prevent unbounded memory usage:
  - `MAX_REASONING_CHARS` for buffered reasoning
  - `MAX_BUFFERED_FINAL_CHARS` for buffered final output

