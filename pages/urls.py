from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("notebook/", views.posts, name="posts"),
    path("notebook/<slug:slug>/", views.post, name="post"),
    # Content router: serves /about.html, /papers/, /teaching/syllabus.html, etc.
    path("<path:req_path>", views.content_router, name="content"),
]
