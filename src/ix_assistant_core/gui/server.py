from __future__ import annotations

import argparse
import json
import mimetypes
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ix_assistant_core.assistant import AssistantSession, GabriellaAssistant
from ix_assistant_core.identity import ASSISTANT_NAME, PROJECT_NAME, WAKE_PHRASE
from ix_assistant_core.models import InputMode


class GabriellaHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], state_dir: Path | None, persist: bool) -> None:
        super().__init__(server_address, GabriellaRequestHandler)
        assistant = GabriellaAssistant.default(state_dir=state_dir, persist=persist)
        self.session = AssistantSession(assistant=assistant)
        self.state_dir = state_dir
        self.persist = persist


class GabriellaRequestHandler(BaseHTTPRequestHandler):
    server: GabriellaHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send_static("index.html")
            return
        if parsed.path.startswith("/static/"):
            self._send_static(parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/api/health":
            self._send_json(
                {
                    "project": PROJECT_NAME,
                    "assistant": ASSISTANT_NAME,
                    "wake_phrase": WAKE_PHRASE,
                    "status": "ready",
                    "voice_input": "browser-speech-recognition",
                    "voice_output": "browser-speech-synthesis",
                    "brain": "IX-Gabriella-Brain integrated",
                    "llm_layer": self.server.session.assistant.llm.provider.mode.value,
                    "llm_stack_health": self.server.session.assistant.llm.health().to_dict(),
                }
            )
            return
        if parsed.path == "/api/state":
            self._send_json(self.server.session.snapshot())
            return
        if parsed.path == "/api/receipts":
            payload = [record.to_dict() for record in self.server.session.assistant.receipts.records()]
            self._send_json({"receipts": payload})
            return
        if parsed.path == "/api/export/receipts":
            data = self.server.session.assistant.export_receipts().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=ix-gabriella-receipts.json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            payload = self._read_json()
            text = str(payload.get("text", ""))
            confidence_raw = payload.get("confidence")
            confidence = None if confidence_raw is None else float(confidence_raw)
            alternatives_raw = payload.get("alternatives", [])
            alternatives = tuple(str(item) for item in alternatives_raw if str(item).strip())
            try:
                turn = self.server.session.submit(
                    text,
                    mode=InputMode.VOICE if payload.get("mode") == "voice" else InputMode.TEXT,
                    acoustic_confidence=confidence,
                    alternatives=alternatives,
                )
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._send_json(_turn_payload(turn, self.server.session.snapshot()))
            return
        if parsed.path == "/api/confirm":
            payload = self._read_json()
            approved = bool(payload.get("approved"))
            turn = self.server.session.confirm_pending(approved)
            if turn is None:
                self._send_json({"error": "no pending action"}, status=HTTPStatus.CONFLICT)
                return
            self._send_json(_turn_payload(turn, self.server.session.snapshot()))
            return
        if parsed.path == "/api/correct":
            payload = self._read_json()
            text = str(payload.get("text", ""))
            turn = self.server.session.correct_pending(text)
            if turn is None:
                self._send_json({"error": "no pending action"}, status=HTTPStatus.CONFLICT)
                return
            self._send_json(_turn_payload(turn, self.server.session.snapshot()))
            return
        if parsed.path == "/api/clear-memory":
            self.server.session.assistant.memory.clear()
            self._send_json(self.server.session.snapshot())
            return
        self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_static(self, name: str) -> None:
        safe_name = name.strip("/") or "index.html"
        if ".." in safe_name or safe_name.startswith("/"):
            self._send_json({"error": "invalid static asset"}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            asset = resources.files("ix_assistant_core.gui.static").joinpath(safe_name)
            data = asset.read_bytes()
        except (FileNotFoundError, ModuleNotFoundError):
            self._send_json({"error": "static asset not found"}, status=HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def _turn_payload(turn, snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "turn": turn.to_dict(),
        "assistant_text": turn.response_text,
        "needs_confirmation": turn.status.value == "waiting_for_confirmation",
        "snapshot": snapshot,
    }


def run_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
    state_dir: Path | None = None,
    persist: bool = True,
) -> GabriellaHTTPServer:
    server = GabriellaHTTPServer((host, port), state_dir=state_dir, persist=persist)
    actual_host, actual_port = server.server_address
    url = f"http://{actual_host}:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    print(f"{PROJECT_NAME} local GUI running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping IX-Gabriella local GUI.")
    finally:
        server.server_close()
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the IX-Gabriella local voice/chat GUI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--no-persist", action="store_true")
    args = parser.parse_args(argv)
    run_server(
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
        state_dir=args.state_dir,
        persist=not args.no_persist,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
