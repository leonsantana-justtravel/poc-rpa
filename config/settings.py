"""
Django settings for config project.
Merged with RPA Statue Logic + POC Amazon Proxy Logic.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# Carrega as variáveis do arquivo .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- HELPER PARA TRANSFORMAR STRING DO .ENV EM BOOLEANO ---
def get_env_bool(var_name, default=False):
    return str(os.getenv(var_name, default)).lower() == "true"


# --- HELPER PARA TRANSFORMAR STRING EM LISTA (CSV) ---
def get_env_list(var_name, default=""):
    value = os.getenv(var_name, default)
    if not value:
        return []
    return [item.strip() for item in value.split(",")]


# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-key-dev-only")

# Agora o DEBUG lê do .env corretamente (True/False)
DEBUG = get_env_bool("DEBUG", True)

# Lê a lista de hosts permitidos (ex: localhost,127.0.0.1)
ALLOWED_HOSTS = get_env_list("ALLOWED_HOSTS", "*")


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    # Local apps
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middleware de Log de Erros (Opcional, se tiver)
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- DJANGO REST FRAMEWORK ---
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}

# --- SEGURANÇA CSRF ---
# Importante para chamadas de API de origens diferentes
CSRF_TRUSTED_ORIGINS = get_env_list("CSRF_TRUSTED_ORIGINS", "http://localhost")
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True


# ==============================================================================
# CONFIGURAÇÕES CUSTOMIZADAS DO ROBÔ (RPA)
# ==============================================================================

# 1. Segurança e Acesso
API_KEY = os.getenv("API_KEY")
DECRYPT_KEY = os.getenv("DECRYPT_KEY")

# 2. Configurações do Playwright
# Define se roda com janela (False) ou sem janela (True)
PLAYWRIGHT_HEADLESS = get_env_bool("PLAYWRIGHT_HEADLESS", False)

# 3. Dados de Pagamento (Vindos do RPA Estátua)
PAYMENT_DETAILS = {
    "CARD_NUMBER": os.getenv("CARD_NUMBER"),
    "CARD_CVC": os.getenv("CARD_CVC"),
    "CARD_EXP_MONTH": os.getenv("CARD_EXP_MONTH"),
    "CARD_EXP_YEAR": os.getenv("CARD_EXP_YEAR"),
    "CARD_TYPE": os.getenv("CARD_TYPE"),
}

# 4. Configuração de Proxy (Vindos do POC Amazon)
PROXY_CONFIG = None
if os.getenv("PROXY_SERVER"):
    PROXY_CONFIG = {
        "server": os.getenv("PROXY_SERVER"),
        "username": os.getenv("PROXY_USER"),
        "password": os.getenv("PROXY_PASS"),
    }

# ==============================================================================
# LOGGING (Essencial para Monitoramento)
# ==============================================================================
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": LOG_LEVEL,
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "core": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@justtravel.com"