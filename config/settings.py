# config/settings.py
# Django settings for notaryai project.

import os
import environ
from pathlib import Path # Use pathlib for modern path handling

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    # Define variables and their types/defaults
    DEBUG=(bool, False),
    DATABASE_URL=(str, f'sqlite:///{BASE_DIR / "db.sqlite3"}'), # Use pathlib for database path
    ALLOWED_HOSTS=(list, []),
    STATIC_URL=(str, '/static/'),
    STATIC_ROOT=(str, BASE_DIR / 'static'), # Use pathlib for static root
    MEDIA_URL=(str, '/media/'),
    MEDIA_ROOT=(str, BASE_DIR / 'media'), # Use pathlib for media root
    SECRET_KEY=(str, 'insecure-fallback-key-change-me'), # Fallback for SECRET_KEY
    GEMINI_API_KEY=(str, None), # Gemini API Key
    # Add other potential API keys here, reading from environment
    CREDAS_API_KEY=(str, None),
    PEPS_SANCTIONS_API_KEY=(str, None),
    ZOOM_API_KEY=(str, None),
    ZOOM_API_SECRET=(str, None),

    # --- Google API Settings (Replacing Microsoft Graph) ---
    # These will be used for Google/Gmail integration
    GOOGLE_OAUTH_CLIENT_ID=(str, None),
    GOOGLE_OAUTH_CLIENT_SECRET=(str, None),
    # The redirect URI registered in the Google Cloud Console
    # This should match a URL pattern in your apps/integrations/urls.py
    GOOGLE_OAUTH_REDIRECT_URI=(str, 'http://localhost:8000/integrations/oauth/google/callback/'), # Example default

)

# Read .env file
# Assumes .env is in the project root directory (one level above config)
# Use BASE_DIR / '.env'
environ.Env.read_env(BASE_DIR / '.env')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-&j$z!d%xcx#7b6x#bzv4dp9+kg8h39mpdc^#qjy!!zc@9ik*3o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5', # If using Bootstrap 5

    # Django Allauth (if using for robust auth)
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',

    # Django Storages (if using for cloud storage)
    'storages', # Keep storages if you intend to use cloud storage

    # Local apps (created in the apps directory)
    'apps.accounts',
    'apps.documents',
    'apps.compliance',
    'apps.clients',
    'apps.workflows',
    'apps.integrations',
    'apps.dashboard',
]

# Crispy Forms Settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Django Allauth Settings (if using)
# AUTHENTICATION_BACKENDS = [
#     'django.contrib.auth.backends.ModelBackend', # Required for Django admin
#     'allauth.account.auth_backends.AuthenticationBackend', # Allauth specific
# ]
# SITE_ID = 1 # Required for allauth
# ACCOUNT_EMAIL_VERIFICATION = 'none' # Or 'mandatory'
# ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_USERNAME_REQUIRED = False # Or True
# ACCOUNT_FORMS = {'signup': 'apps.accounts.forms.CustomSignupForm'} # If you customize signup

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'allauth.account.middleware.AccountMiddleware', # Allauth middleware if using
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Project level templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # 'allauth.account.context_processors.account', # Allauth context processor
                # 'allauth.socialaccount.context_processors.socialaccount', # Allauth context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': env.db() # Configured via DATABASE_URL in .env
}


# Password validation
# https://docs.djangoproject.com/en/5.0/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # Ensure this path is correct for your Django version
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = env('STATIC_URL', default='/static/')

# This is the directory where `collectstatic` will gather all static files for deployment.
# In development, the runserver command serves files from STATICFILES_DIRS and app's static directories.
STATIC_ROOT = env('STATIC_ROOT', default=BASE_DIR / 'staticfiles') # Changed to 'staticfiles' to avoid conflict with source 'static' dir

# This setting tells Django where to look for static files IN ADDITION to
# the 'static' subdirectory of each app. This is where your project-level
# static files (like base CSS/JS) should be located.
STATICFILES_DIRS = [
    BASE_DIR / 'static', # Explicitly include your project-level static directory
]

# This setting defines the finders that Django uses to locate static files.
# AppDirectoriesFinder looks in the 'static' dir of each installed app.
# FileSystemFinder looks in the directories listed in STATICFILES_DIRS.
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]


# Media files (User uploaded content)
# https://docs.djangoproject.com/en/5.2/howto/static-files/#serving-files-uploaded-by-a-user-during-development
MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = env('MEDIA_ROOT', default=BASE_DIR / 'media') # Use pathlib




# Default primary key field type
# https://docs.djangoproject.com/en/5.0/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser' # Tell Django to use your custom user model

# Login Redirect URL (after successful login)
# This is where users are redirected after login OR successful registration
LOGIN_REDIRECT_URL = '/' # Changed from '/matters/' to '/' for dashboard

# Logout Redirect URL (after successful logout)
LOGOUT_REDIRECT_URL = '/accounts/login/' # Redirect to the login page after logout (example)


# Gemini AI API Key
GEMINI_API_KEY = env('GEMINI_API_KEY')

# Other Integration API Keys (read from environment)
CREDAS_API_KEY = env('CREDAS_API_KEY', default=None)
PEPS_SANCTIONS_API_KEY = env('PEPS_SANCTIONS_API_KEY', default=None)
ZOOM_API_KEY = env('ZOOM_API_KEY', default=None)
ZOOM_API_SECRET = env('ZOOM_API_SECRET', default=None)

# --- Google API Credentials (Read from environment) ---
GOOGLE_OAUTH_CLIENT_ID = env('GOOGLE_OAUTH_CLIENT_ID', default=None)
GOOGLE_OAUTH_CLIENT_SECRET = env('GOOGLE_OAUTH_CLIENT_SECRET', default=None)
GOOGLE_OAUTH_REDIRECT_URI = env('GOOGLE_OAUTH_REDIRECT_URI', default='http://localhost:8000/integrations/oauth/google/callback/')


# Optional: Email settings (if needed for password reset, etc.)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' # Use console backend for testing
# EMAIL_HOST = env('EMAIL_HOST', default='')
# EMAIL_PORT = env('EMAIL_PORT', default=587)
# EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
# EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='')


# Optional: Django Storages settings (if using cloud storage)
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage' # Example for S3
# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='')
# AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='')
# AWS_S3_FILE_OVERWRITE = False






