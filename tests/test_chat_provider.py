from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from ix_assistant_core.providers.chat import OpenAICompatibleChatProvider


class _ProviderHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        assert "messages" in json.loads(body)
        payload = {"choices": [{"message": {"content": "Provider reply accepted."}}]}
        data = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def test_openai_compatible_provider_uses_configured_endpoint(monkeypatch) -> None:
    server = HTTPServer(("127.0.0.1", 0), _ProviderHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        monkeypatch.setenv("IX_GABRIELLA_CHAT_ENDPOINT", f"http://{host}:{port}/chat")
        monkeypatch.setenv("IX_GABRIELLA_CHAT_MODEL", "local-test-model")
        provider = OpenAICompatibleChatProvider(timeout_seconds=5)
        assert provider.reply(user_text="hello") == "Provider reply accepted."
    finally:
        server.shutdown()
        server.server_close()
