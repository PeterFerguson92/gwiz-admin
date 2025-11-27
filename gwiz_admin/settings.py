from datetime import timedelta
import os
from pathlib import Path
import environ

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from dev.env
environ.Env.read_env(os.path.join(BASE_DIR, "dev.env"))
print("USING " + env("ENVIROMENT") + " SETTINGS")
IS_DEV = env("ENVIROMENT") == "DEV"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("ENABLE_DEBUG") == "True"

ALLOWED_HOSTS = ["localhost"]
if not IS_DEV:
    ALLOWED_HOSTS.append(env("ALLOWED_HOST"))
    CSRF_TRUSTED_ORIGINS = [env("CSRF_TRUSTED_ORIGIN")]

# Application definition
INSTALLED_APPS = [
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "django_resized",
    "rest_framework",
    "corsheaders",
    "homepage",
    "accounts"
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ WhiteNoise for static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gwiz_admin.urls"

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

WSGI_APPLICATION = "gwiz_admin.wsgi.application"

# Database
if IS_DEV:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("PGDATABASE"),
            "USER": env("PGUSER"),
            "PASSWORD": env("PGPASSWORD"),
            "HOST": env("PGHOST"),
            "PORT": env("PGPORT"),
        }
    }
    
AUTH_USER_MODEL = "accounts.User"


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
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
TIME_ZONE = "Europe/Belfast"
USE_I18N = True
USE_L10N = False
USE_TZ = False

# ✅ Static files (CSS, JS)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# Remove bad "admin" dir, unless you have custom admin static files
# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static", "admin")]

# ✅ Media files (S3)
MEDIA_URL = f"https://{env('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com/"

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")
AWS_S3_SIGNATURE_NAME = "s3v4"
AWS_S3_FILE_OVERWRITE = True
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# Security settings (safe for dev)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# Misc
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATE_FORMAT = "d-m-Y"
DATE_INPUT_FORMATS = ["%d-%m-%Y"]
X_FRAME_OPTIONS = "SAMEORIGIN"
XS_SHARING_ALLOWED_METHODS = ["POST", "GET", "OPTIONS", "PUT", "DELETE"]
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")


UNFOLD = {
    "SITE_TITLE": "Gwiz Admin",
    "SITE_HEADER": "Gwiz Dashboard",
    "THEME": "auto",  # light / dark / auto
}

# DRF + JWT Settings
# -------------------------------------------------------------------
# Django REST Framework + SimpleJWT Authentication Settings
#
# REST_FRAMEWORK:
#   - DEFAULT_AUTHENTICATION_CLASSES:
#         Uses JWTAuthentication, meaning every request is checked for
#         an Authorization header like: "Bearer <access_token>".
#
#   - DEFAULT_PERMISSION_CLASSES:
#         By default, all API endpoints require the user to be
#         authenticated. Public endpoints (e.g., login/register)
#         must explicitly set: permission_classes = [AllowAny].
#
# SIMPLE_JWT:
#   - ACCESS_TOKEN_LIFETIME:
#         Access tokens (used for each request) expire after 30 minutes
#         to reduce risk if stolen.
#
#   - REFRESH_TOKEN_LIFETIME:
#         Refresh tokens (used to obtain new access tokens) last 7 days.
#         This allows users to stay logged in without entering credentials.
#
#   - AUTH_HEADER_TYPES:
#         Defines the prefix for JWTs in the Authorization header.
#         Example: "Authorization: Bearer <token>".
# -------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID")