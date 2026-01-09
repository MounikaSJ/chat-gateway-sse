import argparse
import json
import sys
import httpx


def run(base_url: str, prompt: str, model: str, mode: str):
    url = base_url.rstrip("/") + "/chat/completions"

    payload = {
        "model": model,
        "stream": True,
        "mode": mode,
        "messages": [{"role": "user", "content": prompt}],
    }

    current_event = None
    final_text = ""

    with httpx.Client(timeout=None) as client:
        with client.stream("POST", url, json=payload) as r:
            r.raise_for_status()

            for raw in r.iter_lines():
                if raw is None:
                    continue
                line = raw.strip()

                if line == "":
                    current_event = None
                    continue

                if line.startswith("event:"):
                    current_event = line[len("event:") :].strip()
                    continue

                if line.startswith("data:"):
                    data_str = line[len("data:") :].strip()
                    try:
                        data = json.loads(data_str)
                    except Exception:
                        data = {"raw": data_str}

                    print(f"[{current_event}] {data}")

                    if current_event == "final_output_delta":
                        final_text += data.get("text", "")

                    if current_event == "done":
                        print("\n--- FINAL OUTPUT ---")
                        print(final_text.strip() or "(empty)")
                        return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:9000")
    ap.add_argument("--prompt", default="hi")
    ap.add_argument("--model", default="x")
    ap.add_argument("--mode", default="normal")
    args = ap.parse_args()

    try:
        run(args.base_url, args.prompt, args.model, args.mode)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
    except Exception as e:
        print(f"Client error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
