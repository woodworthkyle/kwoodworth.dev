from __future__ import annotations

from typing import Any, Iterable, Optional

from django import template

register = template.Library()


@register.inclusion_tag("pages/widgets/biography.html", takes_context=True)
def biography_widget(context, title: str = "About", bio: Optional[str] = None, links: Optional[Iterable[dict]] = None):
    """Small author/profile widget for a rail."""
    profile = context.get("site_profile", {}) or {}
    bio_text = bio if bio is not None else profile.get("bio", "")
    link_list = list(links) if links is not None else list(profile.get("links", []) or [])
    return {"title": title, "bio": bio_text, "links": link_list}


@register.inclusion_tag("pages/widgets/categories.html", takes_context=True)
def categories_widget(context, title: str = "Categories", tag: str | None = None, tag_labels: dict | None = None, url_name: str = "pages:posts"):
    """Category/tag filter widget for the posts index."""
    labels = tag_labels if tag_labels is not None else (context.get("tag_labels") or {})
    current = tag if tag is not None else context.get("tag")
    return {"title": title, "tag_labels": labels, "current_tag": current, "url_name": url_name}


@register.inclusion_tag("pages/widgets/toc.html", takes_context=True)
def toc_widget(context, title: str = "Contents", target_id: str = "content", toc_id: str = "toc"):
    """Table of contents placeholder; JS fills it."""
    return {"title": title, "target_id": target_id, "toc_id": toc_id}


@register.inclusion_tag("pages/widgets/navigator.html", takes_context=True)
def navigator_widget(context, title: str = "Path", breadcrumbs=None, back_label: str | None = None, back_url: str | None = None):
    """Breadcrumb/path widget (or a simple back link)."""
    crumbs = breadcrumbs if breadcrumbs is not None else context.get("breadcrumbs")
    return {"title": title, "breadcrumbs": crumbs, "back_label": back_label, "back_url": back_url}
