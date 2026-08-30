from __future__ import annotations

import compileall
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path.cwd()
    src_dir = root / "src"
    compile_ok = compileall.compile_dir(str(src_dir), quiet=1) if src_dir.exists() else True
    pytest_result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root, text=True)
    results = {
        "project": "IX-Gabriella",
        "version": "0.1.0-brain-integrated-llm-ready",
        "compileall": compile_ok,
        "pytest_exit_code": pytest_result.returncode,
        "passed": bool(compile_ok) and pytest_result.returncode == 0,
    }
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if results["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
