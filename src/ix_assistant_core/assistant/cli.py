from __future__ import annotations

import argparse
import json

from ix_assistant_core.assistant.engine import GabriellaAssistant


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="IX-Gabriella governed assistant CLI")
    parser.add_argument("text", nargs="+", help="User text to process")
    parser.add_argument("--confirm", help="Optional confirmation reply for review-required actions")
    parser.add_argument("--receipts", action="store_true", help="Print receipt ledger JSON")
    args = parser.parse_args(argv)

    assistant = GabriellaAssistant.default()
    turn = assistant.handle_text(" ".join(args.text))
    if args.confirm:
        turn = assistant.confirm(turn, args.confirm)
    print(json.dumps(turn.to_dict(), indent=2, sort_keys=True))
    if args.receipts:
        print(assistant.receipts.export_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
