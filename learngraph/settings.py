import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env', override=False)
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith('change-me'):
    raise ImproperlyConfigured('Set a random SECRET_KEY of at least 50 characters in .env.')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
if '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Use explicit ALLOWED_HOSTS; wildcard is disabled.')
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if h.strip()]
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
STATIC_ROOT = BASE_DIR / 'staticfiles'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'learning',
    'academy',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'academy.telemetry.ActorMiddleware',
    'learning.security.RequestSecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'learngraph.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'learning.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'learngraph.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not DATABASE_URL:
    raise ImproperlyConfigured('DATABASE_URL is required. Run configure.py and use the PostgreSQL Docker setup.')
DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=60, conn_health_checks=True)}
TEST_CONFIGURATION = os.environ.get('_TEST_CONFIGURATION') == '1' and DEBUG
if not TEST_CONFIGURATION and DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
    raise ImproperlyConfigured('This release requires PostgreSQL.')

AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.' + name} for name in ['UserAttributeSimilarityValidator', 'MinimumLengthValidator', 'CommonPasswordValidator', 'NumericPasswordValidator']]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Groq API Key —
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# ── EMAIL SETTINGS ────────────────────────────────────────────────────────────
# ⚠️ Replace with your Gmail and App Password
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL') or EMAIL_HOST_USER or 'noreply@example.com'

# ── AUTH SETTINGS ─────────────────────────────────────────────────────────────
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Verification code expiry (minutes)
VERIFICATION_CODE_EXPIRY = 10

EMAIL_TIMEOUT = 15
GROQ_MODEL = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')

REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
CACHES = {'default': {'BACKEND':'django.core.cache.backends.redis.RedisCache','LOCATION':REDIS_URL}}

AI_DAILY_REQUEST_LIMIT = int(os.environ.get('AI_DAILY_REQUEST_LIMIT', '100'))

STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://localhost:8000').rstrip('/')
BRAND_NAME = os.environ.get('BRAND_NAME', 'LearnGraph AI')
TRUST_PROXY = os.environ.get('TRUST_PROXY', 'False').lower() == 'true'
if TRUST_PROXY:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
if not DEBUG and not PUBLIC_BASE_URL.startswith('https://'):
    raise ImproperlyConfigured('Production PUBLIC_BASE_URL must use HTTPS.')
if not DEBUG and EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
    raise ImproperlyConfigured('Production requires the SMTP email backend.')

# Explicit local font bundle makes certificate appearance independent of host fonts.
SESSION_COOKIE_AGE = 60 * 60 * 12
PASSWORD_RESET_TIMEOUT = 60 * 60
