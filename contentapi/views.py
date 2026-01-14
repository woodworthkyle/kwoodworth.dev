from django.db import transaction
from django.utils.dateparse import parse_datetime

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Doc, DocHistory


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def upsert_doc(request):
    p = request.data

    for k in ("doc_key", "content_hash", "html"):
        if k not in p:
            return Response({"error": f"missing field: {k}"}, status=status.HTTP_400_BAD_REQUEST)

    doc_key = str(p["doc_key"])
    content_hash = str(p["content_hash"])
    html = str(p["html"])

    title = str(p.get("title", "") or "")
    slug = str(p.get("slug", "") or "")
    tags = p.get("tags", []) or []
    if not isinstance(tags, list):
        return Response({"error": "tags must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    client_version = int(p.get("version", 0) or 0)
    client_updated_at = parse_datetime(p["updated_at"]) if p.get("updated_at") else None

    with transaction.atomic():
        doc, created = Doc.objects.select_for_update().get_or_create(
            doc_key=doc_key,
            defaults=dict(
                title=title,
                slug=slug,
                tags=tags,
                html=html,
                content_hash=content_hash,
                client_version=client_version,
                client_updated_at=client_updated_at,
                server_version=1,
            ),
        )

        if not created:
            if doc.content_hash == content_hash:
                # No-op idempotency
                return Response({"status": "no_change", "server_version": doc.server_version})

            # Optional: history snapshot
            DocHistory.objects.create(
                doc=doc,
                server_version=doc.server_version,
                content_hash=doc.content_hash,
                html=doc.html,
            )

            # Last-write-wins update
            doc.title = title
            doc.slug = slug
            doc.tags = tags
            doc.html = html
            doc.content_hash = content_hash
            doc.client_version = client_version
            doc.client_updated_at = client_updated_at
            doc.server_version += 1
            doc.save()

        return Response(
            {"status": "created" if created else "updated", "server_version": doc.server_version},
            status=status.HTTP_200_OK,
        )
