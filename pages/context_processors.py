import json
from .nav import build_nav_tree

def site_nav(request):
    tree = build_nav_tree()
    def node_to_dict(n):
        return {"title": n.title, "url": n.url, "children": [node_to_dict(c) for c in n.children]}
    return {
        "site_nav_tree": tree,
        "site_nav_tree_json": json.dumps([node_to_dict(n) for n in tree]),
        # Used by rail widgets (can be customized later)
        "site_profile": {
            "bio": "Short author box area for context + external links.",
            "links": [
                {"label": "Bio", "href": "/", "external": False},
                {"label": "RSS", "href": "#", "external": False},
                {"label": "Scholar", "href": "#", "external": False},
            ],
        },
    }
