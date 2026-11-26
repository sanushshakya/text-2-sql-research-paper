"""Offline test of the OpenAI-compatible backend against a local fake server (no key, no internet)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

pytest.importorskip("openai")
from t2s import config, llm  # noqa: E402


def _server(state):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["bodies"].append(body)
            if len(state["bodies"]) == 1:                      # first call: rate limited
                self.send_response(429); self.send_header("retry-after", "0"); self.end_headers()
                self.wfile.write(b'{"error": {"message": "slow down"}}'); return
            out = {"id": "x", "object": "chat.completion", "created": 0, "model": "m",
                   "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": "SELECT 1"}}],
                   "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}}
            self.send_response(200); self.send_header("content-type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps(out).encode())
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_openai_compatible_retries_429_and_sends_temperature(monkeypatch):
    state = {"bodies": []}
    srv = _server(state)
    monkeypatch.setattr(config, "PROVIDER", "openai_compatible")
    monkeypatch.setitem(config.PROVIDERS, "openai_compatible",
                        {"base_url": f"http://127.0.0.1:{srv.server_port}/v1", "key_env": "T2S_TEST_KEY", "default_model": None})
    monkeypatch.setattr(config, "MODEL_ID", "fake-model")
    monkeypatch.setenv("T2S_TEST_KEY", "k")
    reply = llm.make_llm().complete("sys", "user question")
    assert reply.text == "SELECT 1" and (reply.input_tokens, reply.output_tokens) == (7, 3)
    assert len(state["bodies"]) == 2                            # one 429, then success
    b = state["bodies"][-1]
    assert b["temperature"] == 0 and b["messages"][0] == {"role": "system", "content": "sys"}
    srv.shutdown()


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.setattr(config, "PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        llm.make_llm()
