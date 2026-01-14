from datetime import date
from django.core.management.base import BaseCommand

from pages.models import Post, Tag


class Command(BaseCommand):
    help = "Seed demo posts + tags into the SQLite database"

    def handle(self, *args, **kwargs):
        tags = {
            "ai": "AI",
            "llms": "LLMs",
            "writing": "Writing",
            "fitness": "Fitness",
        }
        tag_objs = {}
        for slug, name in tags.items():
            t, _ = Tag.objects.update_or_create(slug=slug, defaults={"name": name})
            tag_objs[slug] = t

        p1, _ = Post.objects.update_or_create(
            slug="a-little-less-conversation",
            defaults=dict(
                title="A little less conversation: from prompting to programming",
                summary="Prompting is fine for conversation. Building things requires learning to program models.",
                body_html="<h2>One</h2><p>Hello from SQLite.</p><h2>Two</h2><p>More content.</p><h3>Two A</h3><p>Subheading.</p><h2>Three</h2><p>Close.</p>",
                date=date(2026, 1, 4),
                is_published=True,
            ),
        )
        p1.tags.set([tag_objs["ai"], tag_objs["llms"], tag_objs["writing"]])

        p2, _ = Post.objects.update_or_create(
            slug="the-95-percent-myth",
            defaults=dict(
                title="The 95% myth",
                summary="How a tiny study became one of the most persistent myths in nutrition.",
                body_html="<h2>Claim</h2><p>What people repeat.</p><h2>Origin</h2><p>Where it came from.</p><h2>Reality</h2><p>What it actually implies.</p>",
                date=date(2023, 12, 27),
                is_published=True,
            ),
        )
        p2.tags.set([tag_objs["fitness"]])

        p3, _ = Post.objects.update_or_create(
            slug="after-agents",
            defaults=dict(
                title="After agents",
                summary="From agents to ecosystems: what orchestration really means in practice.",
                body_html="<h2>Agents</h2><p>A mental model that helped—and then didn’t.</p><h2>Ecosystems</h2><p>Why composition beats monoliths.</p>",
                date=date(2025, 1, 4),
                is_published=True,
            ),
        )
        p3.tags.set([tag_objs["ai"], tag_objs["llms"]])

        self.stdout.write(self.style.SUCCESS("Seeded demo tags + posts."))
