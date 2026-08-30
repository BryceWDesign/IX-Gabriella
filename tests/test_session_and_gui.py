from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen
import json

from ix_assistant_core.assistant import AssistantSession, GabriellaAssistant
from ix_assistant_core.gui.server import GabriellaHTTPServer
from ix_assistant_core.models import ActionStatus


def test_session_confirms_pending_email(tmp_path: Path) -> None:
    assistant = GabriellaAssistant.default(state_dir=tmp_path, persist=True)
    session = AssistantSession(assistant=assistant)
    first = session.submit("email Sam that I will be late")
    assert first.status == ActionStatus.WAITING_FOR_CONFIRMATION
    second = session.submit("yes confirm")
    assert second.status == ActionStatus.COMPLETED
    assert assistant.local_store.list_records(kind="email_draft")


def test_session_corrects_pending_smart_home_action() -> None:
    session = AssistantSession()
    first = session.submit("turn off the kitchen lights")
    assert first.status == ActionStatus.WAITING_FOR_CONFIRMATION
    corrected = session.submit("no I meant turn on the kitchen lights")
    assert corrected.intent.slots["requested_state"] == "on"


def test_gui_health_and_chat_endpoint(tmp_path: Path) -> None:
    server = GabriellaHTTPServer(("127.0.0.1", 0), state_dir=tmp_path, persist=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        health = urlopen(f"http://{host}:{port}/api/health", timeout=5).read().decode("utf-8")
        assert "IX-Gabriella" in health
        payload = json.dumps({"text": "Hey Gabriella take a note test GUI", "mode": "text"}).encode("utf-8")
        request = Request(
            f"http://{host}:{port}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        response = json.loads(urlopen(request, timeout=5).read().decode("utf-8"))
        assert response["turn"]["intent"]["kind"] == "create_note"
        assert "Note saved locally" in response["assistant_text"]
    finally:
        server.shutdown()
        server.server_close()
