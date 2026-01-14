from django.db import models

class Doc(models.Model):
    doc_key = models.CharField(max_length=255, unique=True, db_index=True)
    title = models.TextField(blank=True, default="")
    slug = models.CharField(max_length=255, blank=True, default="", db_index=True)
    tags = models.JSONField(blank=True, default=list)

    html = models.TextField(blank=True, default="")
    content_hash = models.CharField(max_length=64, db_index=True)

    client_version = models.IntegerField(default=0)
    client_updated_at = models.DateTimeField(null=True, blank=True)

    server_version = models.BigIntegerField(default=0)
    server_updated_at = models.DateTimeField(auto_now=True)

class DocHistory(models.Model):
    doc = models.ForeignKey(Doc, on_delete=models.CASCADE, related_name="history")
    server_version = models.BigIntegerField()
    content_hash = models.CharField(max_length=64)
    html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
