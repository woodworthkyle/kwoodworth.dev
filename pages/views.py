from __future__ import annotations

from pathlib import Path
from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from .models import Post, Tag

HTML_EXTS = {".html", ".htm"}


def _safe_join(root: Path, req_path: str) -> Path:
    candidate = (root / req_path).resolve()
    root_resolved = root.resolve()
    if root_resolved not in candidate.parents and candidate != root_resolved:
        raise Http404("Invalid path")
    return candidate


def _read_html(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def home(request):
    root = settings.CONTENT_ROOT
    home_dir = root / "home"
    index = home_dir / "index.html"
    if index.exists():
        return render(
            request,
            "pages/content_file.html",
            {
                "title": "Home",
                "html": _read_html(index),
                "breadcrumbs": [("Home", "/")],
            },
        )
    return render(request, "pages/home_fallback.html")


def posts(request):
    tag = (request.GET.get("tag") or "all").lower()

    qs = Post.objects.filter(is_published=True).prefetch_related("tags")

    if tag != "all":
        qs = qs.filter(tags__slug=tag)

    tag_objs = Tag.objects.all()
    tag_labels = {"all": "All", **{t.slug: t.name for t in tag_objs}}

    ctx = {
        "posts": qs,
        "tag": tag,
        "tag_labels": tag_labels,
    }
    return render(request, "pages/posts.html", ctx)


def post(request, slug: str):
    try:
        p = Post.objects.prefetch_related("tags").get(slug=slug, is_published=True)
    except Post.DoesNotExist:
        raise Http404("Post not found")
    return render(request, "pages/post_db.html", {"post": p})


def content_router(request, req_path: str):
    root: Path = settings.CONTENT_ROOT

    # Support extensionless URLs by trying .html
    target = _safe_join(root, req_path)
    if not target.exists():
        no_slash = req_path.rstrip("/")
        if not Path(no_slash).suffix:
            maybe = _safe_join(root, no_slash + ".html")
            if maybe.exists():
                target = maybe
            else:
                maybe_dir = _safe_join(root, no_slash)
                if maybe_dir.exists() and maybe_dir.is_dir():
                    target = maybe_dir
        else:
            raise Http404("Not found")

    if target.is_dir():
        index = target / "index.html"
        if index.exists():
            title = target.name.replace("-", " ").replace("_", " ").title()
            return render(
                request,
                "pages/content_file.html",
                {
                    "title": title,
                    "html": _read_html(index),
                    "breadcrumbs": _breadcrumbs_for_dir(req_path),
                },
            )

        items = _list_dir(target, req_path)
        title = target.name.replace("-", " ").replace("_", " ").title()
        return render(
            request,
            "pages/content_dir.html",
            {
                "title": title,
                "dir_path": "/" + req_path.rstrip("/") + "/",
                "items": items,
                "breadcrumbs": _breadcrumbs_for_dir(req_path),
            },
        )

    if target.is_file() and target.suffix.lower() in HTML_EXTS:
        title = target.stem.replace("-", " ").replace("_", " ").title()
        return render(
            request,
            "pages/content_file.html",
            {
                "title": title,
                "html": _read_html(target),
                "breadcrumbs": _breadcrumbs_for_file(req_path),
            },
        )

    raise Http404("Unsupported file type")


def _breadcrumbs_for_dir(req_path: str):
    parts = [p for p in req_path.split("/") if p]
    crumbs = [("Home", "/")]
    acc = ""
    for part in parts:
        acc += part + "/"
        crumbs.append((part.replace("-", " ").replace("_", " ").title(), "/" + acc))
    return crumbs


def _breadcrumbs_for_file(req_path: str):
    parts = [p for p in req_path.split("/") if p]
    crumbs = [("Home", "/")]
    acc = ""
    for part in parts[:-1]:
        acc += part + "/"
        crumbs.append((part.replace("-", " ").replace("_", " ").title(), "/" + acc))
    last = parts[-1]
    crumbs.append(
        (
            Path(last).stem.replace("-", " ").replace("_", " ").title(),
            "/" + "/".join(parts),
        )
    )
    return crumbs


def _list_dir(target: Path, req_path: str):
    ignore = set(getattr(settings, "CONTENT_IGNORE", set()))
    dirs = []
    files = []
    prefix = "/" + req_path.rstrip("/") + "/"
    for p in sorted(target.iterdir(), key=lambda x: x.name.lower()):
        if p.name.startswith(".") or p.name in ignore:
            continue
        if p.is_dir():
            dirs.append(
                {
                    "kind": "dir",
                    "title": p.name.replace("-", " ").replace("_", " ").title(),
                    "url": prefix + p.name + "/",
                }
            )
        elif p.is_file() and p.suffix.lower() in HTML_EXTS:
            files.append(
                {
                    "kind": "file",
                    "title": p.stem.replace("-", " ").replace("_", " ").title(),
                    "url": prefix + p.name,
                }
            )
    return dirs + files
