import threading
import time
import socket
import unittest

import httpx
import uvicorn


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _run_uvicorn(app, host: str, port: int):
    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


class TestGatewaySSEIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up_port = _free_port()
        cls.gw_port = _free_port()

        # 1) Start upstream
        import mock_upstream
        cls._up_thread = threading.Thread(
            target=_run_uvicorn,
            args=(mock_upstream.app, "127.0.0.1", cls.up_port),
            daemon=True,
        )
        cls._up_thread.start()

        # Wait until upstream accepts connections
        up_url = f"http://127.0.0.1:{cls.up_port}/chat/completions"
        for _ in range(50):
            try:
                r = httpx.post(
                    up_url,
                    json={"model": "x", "stream": True, "messages": [{"role": "user", "content": "hi"}]},
                    timeout=1.0,
                )
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Upstream did not start")

        # 2) Import gateway and point it at our upstream port
        import server
        server.UPSTREAM_BASE_URL = f"http://127.0.0.1:{cls.up_port}"

        # 3) Start gateway
        cls._gw_thread = threading.Thread(
            target=_run_uvicorn,
            args=(server.app, "127.0.0.1", cls.gw_port),
            daemon=True,
        )
        cls._gw_thread.start()

        # Wait until gateway /health is ready
        gw_health = f"http://127.0.0.1:{cls.gw_port}/health"
        for _ in range(50):
            try:
                r = httpx.get(gw_health, timeout=1.0)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("Gateway did not start")

    def test_gateway_stream_smoke(self):
        url = f"http://127.0.0.1:{self.gw_port}/chat/completions"
        payload = {"model": "x", "stream": True, "messages": [{"role": "user", "content": "hi"}]}

        seen = set()
        final_text = ""

        with httpx.Client(timeout=10.0) as client:
            with client.stream("POST", url, json=payload) as resp:
                self.assertEqual(resp.status_code, 200)

                current_event = None
                for line in resp.iter_lines():
                    if not line:
                        continue

                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                        continue

                    if line.startswith("data:") and current_event:
                        data_str = line.split(":", 1)[1].strip()
                        seen.add(current_event)

                        if current_event == "final_output_delta":
                            try:
                                obj = httpx.Response(200, content=data_str).json()
                                final_text += obj.get("text", "")
                            except Exception:
                                pass

                        if current_event == "done":
                            break

        self.assertIn("prompt_summary", seen)
        self.assertIn("reasoning_summary", seen)
        self.assertIn("final_output_delta", seen)
        self.assertIn("done", seen)
        self.assertIn("Hi!", final_text)


if __name__ == "__main__":
    unittest.main()
