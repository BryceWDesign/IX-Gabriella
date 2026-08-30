from __future__ import annotations

import json
import py_compile
from pathlib import Path
from typing import Any

from .hashing import stable_hash, utc_now_iso

FORBIDDEN_MARKERS = ("TO" + "DO", "FIX" + "ME", "PLACE" + "HOLDER", "ST" + "UB", "NOT " + "IMPLEMENTED", "COMING " + "SOON")
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", "dist", "build"}


def iter_repo_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return tuple(sorted(files))


def compile_python(root: Path) -> tuple[str, ...]:
    compiled: list[str] = []
    for path in sorted((root / "src").rglob("*.py")):
        py_compile.compile(str(path), doraise=True)
        compiled.append(str(path.relative_to(root)))
    for path in sorted((root / "scripts").rglob("*.py")):
        py_compile.compile(str(path), doraise=True)
        compiled.append(str(path.relative_to(root)))
    return tuple(compiled)


def scan_forbidden_markers(root: Path) -> tuple[str, ...]:
    findings: list[str] = []
    for path in iter_repo_files(root):
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        upper = text.upper()
        for marker in FORBIDDEN_MARKERS:
            if marker in upper:
                findings.append(f"{path.relative_to(root)}:{marker}")
    return tuple(findings)


def build_manifest(root: Path) -> dict[str, Any]:
    entries: dict[str, str] = {}
    for path in iter_repo_files(root):
        if path.name == "RELEASE_MANIFEST.sha256.json":
            continue
        data = path.read_bytes()
        entries[str(path.relative_to(root))] = stable_hash({"bytes_sha256": __import__("hashlib").sha256(data).hexdigest()})
    return {"created_at": utc_now_iso(), "entries": entries, "file_count": len(entries)}


def run_quality_gate(root: Path) -> dict[str, Any]:
    compiled = compile_python(root)
    findings = scan_forbidden_markers(root)
    manifest = build_manifest(root)
    result = {
        "project": "IX-Gabriella-Brain",
        "version": "0.1.0",
        "created_at": utc_now_iso(),
        "compile_passed": True,
        "compiled_files": list(compiled),
        "forbidden_marker_findings": list(findings),
        "manifest_file_count": manifest["file_count"],
        "overall_passed": not findings,
    }
    (root / "RELEASE_MANIFEST.sha256.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (root / "QUALITY_GATE.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result
