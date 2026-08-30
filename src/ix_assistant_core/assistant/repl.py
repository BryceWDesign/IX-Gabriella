from __future__ import annotations

from ix_assistant_core.assistant.session import AssistantSession
from ix_assistant_core.identity import ASSISTANT_NAME


def main() -> int:
    session = AssistantSession()
    print(f"{ASSISTANT_NAME} local chat. Type /quit to exit. Type yes/no to confirm pending actions.")
    while True:
        try:
            text = input("You: ").strip()
        except EOFError:
            print()
            return 0
        if text.lower() in {"/quit", "quit", "exit"}:
            return 0
        if not text:
            continue
        try:
            turn = session.submit(text)
        except ValueError as exc:
            print(f"Gabriella: {exc}")
            continue
        print(f"Gabriella: {turn.response_text}")
        if turn.confirmation_prompt:
            print("Gabriella is waiting for yes/no approval or a correction.")


if __name__ == "__main__":
    raise SystemExit(main())
