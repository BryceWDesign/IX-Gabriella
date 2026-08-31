from __future__ import annotations

import compileall
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_MARKERS = ("TO" "DO", "FIX" "ME", "Woo" "ster", "woo" "ster")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_files() -> list[Path]:
    return sorted(
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and ".mypy_cache" not in p.parts
        and ".ruff_cache" not in p.parts
        and p.suffix != ".pyc"
    )


def scan_forbidden(files: list[Path]) -> dict[str, list[str]]:
    findings: dict[str, list[str]] = {}
    for path in files:
        if path.name in {"RELEASE_MANIFEST.sha256.json", "QUALITY_GATE.json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hits = [marker for marker in FORBIDDEN_MARKERS if marker in text]
        if hits:
            findings[str(path.relative_to(ROOT)).replace("\\", "/")] = hits
    return findings


def main() -> int:
    compile_ok = compileall.compile_dir(str(ROOT / "src"), quiet=1)
    pytest = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, text=True)
    llm_evals = subprocess.run([sys.executable, "scripts/run_llm_evals.py"], cwd=ROOT, text=True)
    files = tracked_files()
    forbidden = scan_forbidden(files)
    manifest = {
        str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p)
        for p in files
        if p.name not in {"RELEASE_MANIFEST.sha256.json", "QUALITY_GATE.json"}
    }
    (ROOT / "RELEASE_MANIFEST.sha256.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    summary = {
        "project": "IX-Gabriella",
        "version": "0.1.0-embedded-model",
        "compileall": compile_ok,
        "pytest_exit_code": pytest.returncode,
        "llm_eval_exit_code": llm_evals.returncode,
        "manifest_entries": len(manifest),
        "forbidden_marker_findings": forbidden,
        "passed": compile_ok and pytest.returncode == 0 and llm_evals.returncode == 0 and not forbidden,
    }
    (ROOT / "QUALITY_GATE.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
