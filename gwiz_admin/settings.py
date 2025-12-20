import os
from datetime import timedelta
from pathlib import Path

import environ
from django.urls import reverse_lazy

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from dev.env
environ.Env.read_env(os.path.join(BASE_DIR, "dev.env"))
print("USING " + env("ENVIROMENT") + " SETTINGS")
IS_DEV = env("ENVIROMENT") == "DEV"

LOG_LEVEL = env("LOG_LEVEL", default=os.environ.get("LOG_LEVEL", "INFO")).upper()
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

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
    "accounts",
    "booking",
    "drf_spectacular",
    "drf_spectacular_sidecar",
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

WSGI_APPLICATION = "gwiz_admin.wsgi.application"

# Database (always Postgres, values pulled from env)
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
STATICFILES_DIRS = [BASE_DIR / "gwiz_admin" / "static"]

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


ADMIN_STATIC_BASE = f"{STATIC_URL}admin/"
PUBLIC_SITE_URL = env("PUBLIC_SITE_URL", default="/")
API_REFERENCE_URL = env("API_REFERENCE_URL", default="https://gwiz.fit/docs")
ADMIN_SITE_ICON = env("ADMIN_SITE_ICON", default=f"{ADMIN_STATIC_BASE}brand/icon.svg")
ADMIN_SITE_FAVICON = env("ADMIN_SITE_FAVICON", default=ADMIN_SITE_ICON)

UNFOLD = {
    "SITE_TITLE": "FSxCG Admin",
    "SITE_HEADER": "FSxCG Admin",
    "SITE_SUBHEADER": "Admin Dashboard",
    "SITE_URL": reverse_lazy("admin:index"),
    "SITE_ICON": ADMIN_SITE_ICON,
    "SITE_DROPDOWN": [
        {
            "title": "View public site",
            "link": PUBLIC_SITE_URL,
            "icon": "travel_explore",
        },
        {"title": "API reference", "link": API_REFERENCE_URL, "icon": "terminal"},
    ],
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": ADMIN_SITE_FAVICON,
        }
    ],
    "THEME": "auto",
    "COLORS": {
        "base": {
            "50": "#f8fafc",
            "100": "#f1f5f9",
            "200": "#e2e8f0",
            "300": "#cbd5f5",
            "400": "#94a3b8",
            "500": "#64748b",
            "600": "#475569",
            "700": "#334155",
            "800": "#1e293b",
            "900": "#0f172a",
            "950": "#020617",
        },
        "primary": {
            "50": "#eef2ff",
            "100": "#e0e7ff",
            "200": "#c7d2fe",
            "300": "#a5b4fc",
            "400": "#818cf8",
            "500": "#6366f1",
            "600": "#4f46e5",
            "700": "#4338ca",
            "800": "#3730a3",
            "900": "#312e81",
            "950": "#1e1b4b",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-700)",
            "default-dark": "var(--color-base-200)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "ENVIRONMENT": "Development" if IS_DEV else "Live",
    "ENVIRONMENT_TITLE_PREFIX": "DEV · " if IS_DEV else "",
    "STYLES": [f"{ADMIN_STATIC_BASE}css/unfold-overrides.css"],
    "ACCOUNT": {
        "navigation": [
            {
                "title": "Profile & password",
                "link": reverse_lazy("admin:password_change"),
            },
            {"title": "Support", "link": "mailto:support@gwiz.fit"},
        ]
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Overview",
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "space_dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": "Bookings",
                        "icon": "event_available",
                        "link": reverse_lazy("admin:booking_booking_changelist"),
                    },
                    {
                        "title": "Class sessions",
                        "icon": "calendar_month",
                        "link": reverse_lazy("admin:booking_classsession_changelist"),
                    },
                ],
            },
            {
                "title": "Programs",
                "collapsible": True,
                "items": [
                    {
                        "title": "Fitness classes",
                        "icon": "fitness_center",
                        "link": reverse_lazy("admin:booking_fitnessclass_changelist"),
                    },
                    {
                        "title": "Recurrence rules",
                        "icon": "autorenew",
                        "link": reverse_lazy("admin:booking_recurrencerule_changelist"),
                    },
                ],
            },
            {
                "title": "People",
                "collapsible": True,
                "items": [
                    {
                        "title": "Members",
                        "icon": "group",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "Trainers",
                        "icon": "diversity_3",
                        "link": reverse_lazy("admin:homepage_trainer_changelist"),
                    },
                    {
                        "title": "Team",
                        "icon": "handshake",
                        "link": reverse_lazy("admin:homepage_team_changelist"),
                    },
                ],
            },
            {
                "title": "Content",
                "collapsible": True,
                "separator": True,
                "items": [
                    {
                        "title": "Homepage",
                        "icon": "home",
                        "link": reverse_lazy("admin:homepage_homepage_changelist"),
                    },
                    {
                        "title": "Banners",
                        "icon": "collections",
                        "link": reverse_lazy("admin:homepage_banner_changelist"),
                    },
                    {
                        "title": "Services",
                        "icon": "auto_awesome",
                        "link": reverse_lazy("admin:homepage_service_changelist"),
                    },
                    {
                        "title": "FAQs",
                        "icon": "quiz",
                        "link": reverse_lazy("admin:homepage_faq_changelist"),
                    },
                    {
                        "title": "Contact leads",
                        "icon": "mail",
                        "link": reverse_lazy("admin:homepage_contact_changelist"),
                    },
                    {
                        "title": "Footer",
                        "icon": "widgets",
                        "link": reverse_lazy("admin:homepage_footer_changelist"),
                    },
                ],
            },
        ],
    },
    "LOGIN": {"image": f"{ADMIN_STATIC_BASE}brand/login-illustration.svg"},
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
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Stripe Payments
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_CURRENCY = env("STRIPE_CURRENCY", default="gbp")
STRIPE_PAYMENT_DESCRIPTION_PREFIX = env(
    "STRIPE_PAYMENT_DESCRIPTION_PREFIX",
    default="Gwiz Class Booking",
)

WHATSAPP_NOTIFICATIONS_ENABLED = env.bool(
    "WHATSAPP_NOTIFICATIONS_ENABLED", default=False
)
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default="")
TWILIO_WHATSAPP_FROM = env("TWILIO_WHATSAPP_FROM", default="")
TWILIO_WHATSAPP_TEMPLATE_SID = env("TWILIO_WHATSAPP_TEMPLATE_SID", default="")
TWILIO_WHATSAPP_ADMIN_RECIPIENTS = env.list(
    "TWILIO_WHATSAPP_ADMIN_RECIPIENTS", default=[]
)
TWILIO_WHATSAPP_ADMIN_TEMPLATE_SID = env(
    "TWILIO_WHATSAPP_ADMIN_TEMPLATE_SID", default=""
)

SPECTACULAR_SETTINGS = {
    "TITLE": "Fsxcg Admin API",
    "DESCRIPTION": "Authentication and admin API for Fsxcg.",
    "VERSION": "1.0.0",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID")

# # Default: use console backend in development
# if DEBUG:
#     EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# else:
#     EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

#     EMAIL_HOST = "smtp.sendgrid.net"
#     EMAIL_PORT = 587
#     EMAIL_USE_TLS = True

#     # SendGrid uses 'apikey' as the username, and the actual API key as the password
#     EMAIL_HOST_USER = "apikey"
#     EMAIL_HOST_PASSWORD = os.environ.get("SENDGRID_API_KEY")


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "apikey"  # literally this string
EMAIL_HOST_PASSWORD = os.environ.get("SENDGRID_API_KEY")
SENDGRID_API_KEY = env(
    "SENDGRID_API_KEY", default=os.environ.get("SENDGRID_API_KEY", "")
)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default=os.environ.get("DEFAULT_FROM_EMAIL", "webmaster@localhost"),
)


FRONTEND_RESET_PASSWORD_URL = env(
    "FRONTEND_RESET_PASSWORD_URL",
    default=os.environ.get(
        "FRONTEND_RESET_PASSWORD_URL", "http://localhost:3000/reset-password"
    ),
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": LOG_LEVEL,
            "formatter": "console",
        },
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": LOG_LEVEL,
            "formatter": "verbose",
            "filename": str(LOG_DIR / "application.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
        },
        "request_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "verbose",
            "filename": str(LOG_DIR / "requests.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
        },
    },
    "root": {
        "handlers": ["console", "app_file"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console", "app_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "request_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "booking": {
            "handlers": ["console", "app_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "notifications": {
            "handlers": ["console", "app_file"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
