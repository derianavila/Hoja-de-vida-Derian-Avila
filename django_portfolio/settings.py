from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================
# SEGURIDAD
# =====================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# DEBUG=1 en local, DEBUG=0 en Render
DEBUG = os.getenv("DEBUG", "1") == "1"

# =====================
# HOSTS / CSRF (Render friendly)
# =====================
# Permite tu dominio de Render y también local
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
]

# Si quieres permitir dominios extra, puedes usar ALLOWED_HOSTS env var (opcional)
extra_hosts = os.getenv("ALLOWED_HOSTS", "").strip()
if extra_hosts:
    for h in extra_hosts.split(","):
        h = h.strip()
        if h and h not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(h)

# CSRF para Render
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
]

# Si pones un dominio extra en ALLOWED_HOSTS, también lo agregamos como trusted origin
for host in ALLOWED_HOSTS:
    if host and host not in ["localhost", "127.0.0.1", ".onrender.com"]:
        # Si el host viene como ".midominio.com" o "midominio.com" igual sirve
        h = host.lstrip(".")
        CSRF_TRUSTED_ORIGINS.append(f"https://{h}")
        CSRF_TRUSTED_ORIGINS.append(f"https://*.{h}")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =====================
# APPS
# =====================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cv",
]

# =====================
# MIDDLEWARE
# =====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "django_portfolio.urls"
WSGI_APPLICATION = "django_portfolio.wsgi.application"

# =====================
# TEMPLATES
# =====================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =====================
# DATABASE (LOCAL + RENDER)
# =====================
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # En Render (Postgres)
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,  # SSL en producción
        )
    }
else:
    # En local (SQLite)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# =====================
# PASSWORDS
# =====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================
# I18N
# =====================
LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================
# STATIC FILES
# =====================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# =====================
# MEDIA FILES
# =====================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =====================
# DEFAULT
# =====================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"