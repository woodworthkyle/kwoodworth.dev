import json
from datetime import datetime
from pathlib import Path
from django.conf import settings
from .nav import build_nav_tree


def _content_last_updated_str() -> str:
    override = getattr(settings, "SITE_LAST_UPDATED", "")
    if override:
        return str(override)

    root = Path(getattr(settings, "CONTENT_ROOT", ""))
    if not root.exists():
        return "Unknown"

    ignore = set(getattr(settings, "CONTENT_IGNORE", set()))
    latest_ts = 0.0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part.startswith(".") or part in ignore for part in p.parts):
            continue
        latest_ts = max(latest_ts, p.stat().st_mtime)

    if latest_ts <= 0:
        return "Unknown"

    dt = datetime.fromtimestamp(latest_ts)
    return f"{dt:%B} {dt.day}, {dt:%Y}"


def site_nav(request):
    tree = build_nav_tree()
    def node_to_dict(n):
        return {"title": n.title, "url": n.url, "children": [node_to_dict(c) for c in n.children]}
    profile_defaults = {
        "name": "Your Name",
        "headline": "Short professional headline",
        "bio": "Add a short bio in mysite/settings.py -> SITE_PROFILE.",
        "location": "",
        "email": "",
        "avatar_url": "",
        "links": [],
    }
    configured = getattr(settings, "SITE_PROFILE", {}) or {}
    profile = {**profile_defaults, **configured}
    owner_name = profile.get("name", "Your Name")
    return {
        "site_nav_tree": tree,
        "site_nav_tree_json": json.dumps([node_to_dict(n) for n in tree]),
        "site_profile": profile,
        "site_footer": {
            "owner_name": owner_name,
            "last_updated": _content_last_updated_str(),
        },
    }
