#!/usr/bin/env python3
"""Static checks for the FFR GitHub Pages site."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.tab_targets: list[str] = []
        self.local_refs: list[tuple[str, str]] = []
        self.images: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if "id" in attr:
            self.ids.append(attr["id"])
        if attr.get("data-target"):
            self.tab_targets.append(attr["data-target"])

        for key in ("src", "href"):
            value = attr.get(key)
            if value and is_local_ref(value):
                self.local_refs.append((tag, value))

        if tag == "img":
            self.images.append((attr.get("src", ""), attr.get("alt", "")))


def is_local_ref(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith("#"):
        return False
    return bool(parsed.path)


def resolve_local_ref(value: str) -> Path:
    parsed = urlparse(value)
    return (DOCS / unquote(parsed.path)).resolve()


def ensure_within_docs(path: Path) -> None:
    try:
        path.relative_to(DOCS.resolve())
    except ValueError as exc:
        raise AssertionError(f"Local reference escapes docs/: {path}") from exc


def main() -> int:
    html = INDEX.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)

    required_text = [
        "arXiv:2604.16243",
        "https://arxiv.org/abs/2604.16243",
        "https://github.com/JethroJames/FFR",
    ]
    missing_text = [item for item in required_text if item not in html]
    if missing_text:
        raise AssertionError(f"Missing required public metadata: {missing_text}")

    forbidden = ["Lorem ipsum", "YOUR_DOMAIN", "PAPER_TITLE", "TODO", "FIXME"]
    leaked = [item for item in forbidden if item in html]
    if leaked:
        raise AssertionError(f"Found placeholder text in project page: {leaked}")

    duplicates = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    if duplicates:
        raise AssertionError(f"Duplicate HTML ids: {duplicates}")

    id_set = set(parser.ids)
    missing_targets = [target for target in parser.tab_targets if target not in id_set]
    if missing_targets:
        raise AssertionError(f"Gallery tabs point to missing panels: {missing_targets}")

    for tag, value in parser.local_refs:
        path = resolve_local_ref(value)
        ensure_within_docs(path)
        if not path.exists():
            raise AssertionError(f"Missing local {tag} asset: {value}")

    bad_images = [src for src, alt in parser.images if not alt.strip() or alt.strip().lower() == "image"]
    if bad_images:
        raise AssertionError(f"Images need descriptive alt text: {bad_images}")

    print("[OK] project page metadata present")
    print("[OK] local assets resolve")
    print("[OK] gallery tab targets valid")
    print("[OK] image alt text present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
