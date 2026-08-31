from __future__ import annotations

import argparse
import json

from ix_gabriella_brain import GabriellaBrain
from ix_gabriella_llm import GabriellaLLMEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run IX-Gabriella-LLM deliberation against brain packets")
    parser.add_argument("text", nargs="+", help="User text to deliberate over")
    parser.add_argument("--json", action="store_true", help="Print full deliberation JSON")
    args = parser.parse_args(argv)
    text = " ".join(args.text)
    brain = GabriellaBrain(execute_fast_locally=False)
    packet = brain.think(text, user_id="local-user", channel="cli", session_id="llm-cli")
    result = GabriellaLLMEngine().deliberate(user_text=text, brain_packet=packet.to_dict())
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(result.response_text or result.reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
