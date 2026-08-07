"""
Configurações do projeto Cognize.
Monólito Django simples: contabilidade, cadastro de empresas e gestão de tarefas.
"""
from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv(
    "SECRET_KEY", "django-inseguro-troque-em-producao-cognize-0000000000"
)
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")

# Hosts: locais + domínios do Railway. RAILWAY_PUBLIC_DOMAIN é injetado pela plataforma.
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,.up.railway.app,.railway.app"
).split(",")
_railway_host = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
if _railway_host and _railway_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_host)

# Origens confiáveis para CSRF (Django exige o esquema https://).
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://*.up.railway.app,https://*.railway.app",
).split(",")
if _railway_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_railway_host}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # apps do projeto
    "accounts",
    "empresas",
    "tarefas",
    "core",
]

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

ROOT_URLCONF = "cognize.urls"

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
                "core.context_processors.navegacao",
            ],
        },
    },
]

WSGI_APPLICATION = "cognize.wsgi.application"

# Em produção o Railway injeta DATABASE_URL (Postgres). Localmente cai no SQLite.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise serve os estáticos em produção (comprimidos e versionados).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Segurança atrás do proxy do Railway (TLS é encerrado na borda).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Railway serve HTTPS na borda; o header acima evita loop de redirecionamento.
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in (
        "1", "true", "yes",
    )
    # HSTS é opcional e "irreversível" enquanto ativo — ligue só quando tiver
    # certeza do domínio definitivo (ex.: 31536000 = 1 ano).
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Login / logout
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# ----------------------------------------------------------------------------
# ReceitaWS
# ----------------------------------------------------------------------------
RECEITAWS_BASE_URL = os.getenv(
    "RECEITAWS_BASE_URL", "https://receitaws.com.br/v1/cnpj"
)
# Limite do plano gratuito: 3 consultas por minuto.
RECEITAWS_MAX_POR_MINUTO = int(os.getenv("RECEITAWS_MAX_POR_MINUTO", "3"))
RECEITAWS_JANELA_SEGUNDOS = int(os.getenv("RECEITAWS_JANELA_SEGUNDOS", "60"))
RECEITAWS_TIMEOUT = int(os.getenv("RECEITAWS_TIMEOUT", "20"))

MESSAGE_TAGS = {
    10: "debug",
    20: "info",
    25: "success",
    30: "warning",
    40: "danger",
}
