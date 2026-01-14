from django.urls import path
from .views import upsert_doc
urlpatterns = [
    path("docs/upsert", upsert_doc),
]
