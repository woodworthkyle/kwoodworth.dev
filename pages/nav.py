from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from django.conf import settings

HTML_EXTS = {".html", ".htm"}


@dataclass
class NavNode:
    title: str
    url: str
    children: list["NavNode"] = field(default_factory=list)


def _titleize(stem: str) -> str:
    return stem.replace("-", " ").replace("_", " ").strip().title() or "Page"


def _is_html(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in HTML_EXTS


def build_nav_tree() -> list[NavNode]:
    """Build a navigation tree from CONTENT_ROOT."""
    root: Path = getattr(settings, "CONTENT_ROOT", None)
    if not root or not root.exists():
        return []

    ignore = set(getattr(settings, "CONTENT_IGNORE", set()))

    def iter_dir(dir_path: Path, url_prefix: str) -> list[NavNode]:
        nodes: list[NavNode] = []
        for p in sorted(dir_path.iterdir(), key=lambda x: x.name.lower()):
            if p.name.startswith(".") or p.name in ignore:
                continue
            if p.is_dir():
                child_url = f"{url_prefix}{p.name}/"
                children = iter_dir(p, child_url)
                nodes.append(NavNode(title=_titleize(p.name), url=child_url, children=children))
            elif _is_html(p):
                nodes.append(NavNode(title=_titleize(p.stem), url=f"{url_prefix}{p.name}", children=[]))
        return nodes

    top: list[NavNode] = []
    for p in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        if p.name.startswith(".") or p.name in ignore:
            continue
        if p.is_dir():
            url = f"/{p.name}/"
            children = iter_dir(p, url)
            top.append(NavNode(title=_titleize(p.name), url=url, children=children))
        elif _is_html(p):
            top.append(NavNode(title=_titleize(p.stem), url=f"/{p.name}", children=[]))

    def sort_key(n: NavNode):
        return (0 if n.url == "/home/" else 1, n.title.lower())

    top.sort(key=sort_key)
    return top
