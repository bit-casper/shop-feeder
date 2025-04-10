"""
Django settings for webshop_manager project.

Generated by 'django-admin startproject' using Django 4.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from decouple import config

SECRET_KEY = config('SECRET_KEY')
#FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY')  # Add this to .env

#FERNET_KEYS = [FERNET_KEY]  # For django-fernet-fields

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'django-insecure-13+=e%ib%=(f*k1oi*kdhq(q5w_j05tyfb_yu_*6zct5ib+3fq'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["192.168.86.141", "127.0.0.1", "localhost", "192.168.108.196", "192.168.108.195"]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
#    'rest_framework',
#    'encrypted_model_fields',
    'shops.apps.ShopsConfig',  # Add your app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Authentication settings
LOGIN_URL = '/login/'  # Redirect here when login is required
LOGIN_REDIRECT_URL = '/'  # After login, go to shop list
LOGOUT_REDIRECT_URL = '/login/'  # After logout, go back to login

ROOT_URLCONF = 'webshop_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Add this line
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'webshop_manager.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    # FOR WORK NETWORK
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': 'shop_feeder_dev',
    #     'USER': 'admin',
    #     'PASSWORD': 'password',
    #     'HOST': '192.168.108.196',  # Raspberry Pi IP address
    #     'PORT': '5432',           # Default PostgreSQL port
    # }

    # FOR HOME NETWORK
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'shop_feeder_dev',
        'USER': 'admin',
        'PASSWORD': 'password',
        'HOST': '192.168.86.141',  # Raspberry Pi IP address
        'PORT': '5432',           # Default PostgreSQL port
    }

    
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# FOR WORK NETWORK
# CELERY_BROKER_URL = 'redis://192.168.108.196:6379/0'
# CELERY_RESULT_BACKEND = 'redis://192.168.108.196:6379/0'

# FOR HOME NETWORK
CELERY_BROKER_URL = 'redis://192.168.86.141:6379/0'
CELERY_RESULT_BACKEND = 'redis://192.168.86.141:6379/0'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'





LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}