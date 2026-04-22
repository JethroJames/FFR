#!/usr/bin/env python3
"""Minimal smoke test for the public FFR release."""

from __future__ import annotations

import compileall
import importlib
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check_paths() -> None:
    required = [
        ROOT / "README.md",
        ROOT / "environment.yml",
        ROOT / "configs" / "dataset_config.example.json",
        ROOT / "docs" / "index.html",
        ROOT / "docs" / "app.js",
        ROOT / "docs" / "styles.css",
        ROOT / "docs" / "assets" / "figures" / "teaser-regimes.png",
        ROOT / "docs" / "assets" / "figures" / "method-overview.png",
        ROOT / "docs" / "assets" / "figures" / "case-study.png",
        ROOT / "docs" / "assets" / "figures" / "social-preview.png",
        ROOT / "docs" / "assets" / "papers" / "ffr-paper.pdf",
        ROOT / "docs" / "assets" / "papers" / "ffr-supplement.pdf",
        ROOT / "scripts" / "check_project_page.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required release assets: {missing}")


def check_syntax() -> None:
    ok = compileall.compile_dir(ROOT / "ffr", quiet=1)
    if not ok:
        raise RuntimeError("compileall reported syntax errors under ffr/")


def check_imports() -> None:
    os.environ.setdefault("API_KEY", "smoke-test-key")
    modules = [
        "ffr.train.grpo",
        "ffr.train.sft",
        "ffr.train.rewards",
        "ffr.eval.eval_bench",
        "ffr.teacher.model",
        "ffr.teacher.server",
    ]
    for module_name in modules:
        importlib.import_module(module_name)


def main() -> int:
    try:
        check_paths()
        check_syntax()
        check_imports()
    except ModuleNotFoundError as exc:  # pragma: no cover - smoke script
        print(
            "[FAIL] Missing Python dependency during import check: "
            f"{exc}. Install the environment from environment.yml first.",
            file=sys.stderr,
        )
        return 1
    except Exception as exc:  # pragma: no cover - smoke script
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print("[OK] release assets present")
    print("[OK] python syntax check passed")
    print("[OK] core module imports passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
