from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["kwoodworth.dev","127.0.0.1", "localhost", "129.121.73.31"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "pages",
    "rest_framework",
    "rest_framework.authtoken",
    'contentapi',
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "pages.context_processors.site_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "mysite.wsgi.application"
ASGI_APPLICATION = "mysite.asgi.application"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Chicago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = "/var/www/kwoodworth.dev/static"
STATICFILES_DIRS = [BASE_DIR / "pages" / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Content-driven nav + routing
CONTENT_ROOT = BASE_DIR / "content"
CONTENT_IGNORE = {".git", ".DS_Store", "__pycache__", "notebook"}

# Optional explicit top-nav ordering by root key (dir name or html stem).
# Unlisted items are appended alphabetically.
NAV_TOP_ORDER = [
    "cv",
    "portfolio",
    "hobbies",
    "blog"
]

SITE_PROFILE = {
    "name": "Kyle Woodworth",
    "headline": "Superconducting Electronics Design Engineer",
    #"headline": "Superconducting Electronics Design Engineer\nTriathlete in training.\nFather of two dogs and one child.",
    #Researcher of superconducting and cryogenic systems for quantum information science and particle physics experiments. 
    #"bio": "Triathlete in training. Father of two dogs and one child.",
    "bio": "",
    "location": "Chicago, IL, United States",
    "email": "woodworthkyle@gmail.com",
    "avatar_url": "/static/pages/img/headshot.jpg",
    "links": [
        {"label": "linkedin", "href": "https://www.linkedin.com/in/woodworthkyle", "external": True, "icon_url": "/static/pages/img/icons/linkedin.svg"},
        {"label": "orcid", "href": "https://orcid.org/0009-0006-2697-6927", "external": True, "icon_url": "/static/pages/img/icons/orcid.svg"},
        {"label": "github", "href": "https://github.com/woodworthkyle/", "external": True, "icon_url": "/static/pages/img/icons/github.svg"},
    ],
}

# Optional manual override for footer text; if empty, it is derived from
# the most recently modified file under CONTENT_ROOT.
_today = date.today()
SITE_LAST_UPDATED = f"{_today:%B} {_today.day}, {_today:%Y}"
