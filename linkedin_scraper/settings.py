"""
Django settings for linkedin_scraper project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# این کلید نباید به صورت ثابت در کد باشد. برای محیط پروداکشن، آن را در متغیرهای محیطی سرور ذخیره کنید.
# مثال: SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
# در محیط پروداکشن، این مقدار باید False باشد تا اطلاعات حساس پروژه نمایش داده نشود.
# مثال: DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 't')
DEBUG = True

# برای محیط پروداکشن، به جای '*' آدرس دقیق دامنه‌های خود را وارد کنید.
# مثال: ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
ALLOWED_HOSTS = ['*'] # برای توسعه محلی مناسب است

# آدرس فرانت‌اند را برای CORS اضافه کنید
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080", # اگر فرانت‌اند روی پورت دیگری است، آن را اضافه کنید
    "http://127.0.0.1:8080",
    "https://a-meraji.github.io", # آدرس گیت‌هاب پیجز فرانت‌اند
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders', # اپلیکیشن CORS
    'scraper', # اپلیکیشن اصلی ما
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # میدل‌ور CORS
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'linkedin_scraper.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'linkedin_scraper.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# برای این پروژه به دیتابیس نیازی نداریم، از sqlite پیش‌فرض استفاده می‌کنیم
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# تنظیمات لاگ‌گیری
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
