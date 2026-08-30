from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .brain import GabriellaBrain


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ix-gabriella-brain")
    parser.add_argument("text", nargs="*", help="Request text for IX-Gabriella-Brain")
    parser.add_argument("--state", default=".ix-gabriella-brain/state.json")
    parser.add_argument("--receipts", default=".ix-gabriella-brain/receipts.jsonl")
    parser.add_argument("--json", action="store_true", help="Print full cognitive packet JSON")
    args = parser.parse_args(argv)
    text = " ".join(args.text).strip()
    if not text:
        parser.error("provide text for Gabriella Brain to process")
    brain = GabriellaBrain(state_path=Path(args.state), receipt_path=Path(args.receipts))
    packet = brain.think(text)
    if args.json:
        print(json.dumps(packet.to_dict(), indent=2, sort_keys=True))
    else:
        print(packet.decision.user_message)
        print(f"route={packet.route.route.value} status={packet.decision.status.value} receipt={packet.receipt_hash[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
