from __future__ import annotations

from django.db import models


class Tag(models.Model):
    slug = models.SlugField(unique=True, db_index=True)
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    slug = models.SlugField(unique=True, db_index=True)
    title = models.CharField(max_length=240)
    summary = models.TextField(blank=True)
    body_html = models.TextField()
    date = models.DateField(db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)

    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self) -> str:
        return self.title
