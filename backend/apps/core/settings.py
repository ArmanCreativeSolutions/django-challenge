import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env(BASE_DIR.joinpath(".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS = env.tuple("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "jazzmin",
    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.utils",
    "apps.stadiums",
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd apps
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_celery_results",
    "django_celery_beat",
    "drf_yasg",
]

ROOT_URLCONF = "apps.core.urls"
WSGI_APPLICATION = "apps.core.wsgi.application"
ASGI_APPLICATION = "apps.core.asgi.application"

AUTH_USER_MODEL = "accounts.User"

# Database config
DATABASES = {
    "default": env.db(),
}

# Cache confing
CACHES = {
    "default": env.cache(),
}

# Project middlewares
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Django templates
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
            ],
        },
    },
]

# Authentication backends
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


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR.joinpath("logs/debug.log"),
            "mode": "a",
            "level": "DEBUG",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": True,
        },
        "django.request": {
            "handlers": ["logfile", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "core": {
            "handlers": ["logfile", "console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# Files & MinIO config
LOCALE_PATHS = (BASE_DIR.joinpath("locale"),)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR.joinpath("static")
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.joinpath("media")

# Django cors config
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS")
CORS_ALLOWED_ORIGIN = env.tuple("CORS_ALLOWED_ORIGIN")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://*.arman.dev", "https://*.127.0.0.1"]
USE_X_FORWARDED_HOST = True

# Localization config
LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Celery config
CELERY_TIMEZONE = "Asia/Tehran"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = env("CELERY_BROKER")
CELERY_RESULT_BACKEND = env("CELERY_BACKEND")
CELERY_CACHE_BACKEND = "django-cache"

# SMS Panel Configuration
SMS_PHONE_NUMBER = env("SMS_PHONE_NUMBER")
SMS_CLIENT_ID = env("SMS_CLIENT_ID")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEST_RUNNER = "redgreenunittest.django.runner.RedGreenDiscoverRunner"
