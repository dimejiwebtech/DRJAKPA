

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG')

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',
    'main',
    'blog',
    'dashboard',
    'media_manager',
    'analytics',
    'jakpa_bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.AnalyticsMiddleware',
]

ROOT_URLCONF = 'DR_JAKPA.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DR_JAKPA.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

AUTH_USER_MODEL = 'auth.User'

# SMTP Configuration
EMAIL_BACKEND = 'utils.gmail_backend.GmailAPIBackend'

GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
GMAIL_CLIENT_SECRET_PATH = os.getenv('GMAIL_CLIENT_SECRET_PATH')

EMAIL_HOST_USER = 'drjakpa@gmail.com'
DEFAULT_FROM_EMAIL = 'Dr. Jakpa <drjakpa@gmail.com>'
CONTACT_EMAIL = 'drjakpa@gmail.com'


TINYMCE_DEFAULT_CONFIG = {
    'license_key': 'gpl',
    'height': 500,
    'width': '100%',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'menubar': True,
    'statusbar': True,
    'plugins': '''
        save link image media preview codesample
        table code lists fullscreen insertdatetime nonbreaking
        directionality searchreplace wordcount visualblocks
        visualchars autolink charmap anchor pagebreak
    ''',
    'toolbar': '''
        undo redo | blocks | bold italic underline strikethrough | 
        forecolor backcolor | alignleft aligncenter alignright alignjustify | 
        bullist numlist outdent indent | link image media table | 
        codesample | code fullscreen preview | removeformat
    ''',
    'contextmenu': 'link image table',
    
    'block_formats': 'Paragraph=p; Heading 2=h2; Heading 3=h3; Heading 4=h4; Heading 5=h5; Heading 6=h6; Preformatted=pre',
    
    'content_style': '''
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #1f2937;
            background-color: #ffffff;
            max-width: 100%;
            padding: 16px;
        }
        h2 { font-size: 1.5rem; font-weight: 700; margin-top: 1.25rem; margin-bottom: 0.5rem; color: #111827; }
        h3 { font-size: 1.25rem; font-weight: 700; margin-top: 1rem; margin-bottom: 0.4rem; color: #1f2937; }
        h4 { font-size: 1.125rem; font-weight: 600; margin-top: 0.875rem; margin-bottom: 0.35rem; color: #1f2937; }
        h5 { font-size: 1rem; font-weight: 600; margin-top: 0.75rem; margin-bottom: 0.3rem; color: #374151; }
        h6 { font-size: 0.875rem; font-weight: 600; margin-top: 0.625rem; margin-bottom: 0.25rem; color: #4b5563; }
        p { margin-bottom: 0.75rem; color: #00000; }
        ul, ol { margin-bottom: 0.75rem; padding-left: 1.5rem; color: #374151; }
        li { margin-bottom: 0.25rem; }
        img { max-width: 100%; height: auto; border-radius: 0.375rem; margin: 0.75rem 0; }
        blockquote { border-left: 3px solid #10b981; padding: 0.5rem 0.75rem; margin: 0.75rem 0; font-style: italic; color: #6b7280; background-color: #f9fafb; border-radius: 0 0.25rem 0.25rem 0; }
        code { background-color: #f3f4f6; padding: 0.15rem 0.35rem; border-radius: 0.25rem; color: #dc2626; font-size: 0.9em; }
        pre { background-color: #1f2937; padding: 0.75rem; border-radius: 0.375rem; overflow-x: auto; color: #e5e7eb; }
        a { color: #2563eb; }
        table { border-collapse: collapse; width: 100%; margin: 0.75rem 0; }
        th, td { border: 1px solid #e5e7eb; padding: 0.5rem; color: #374151; }
        th { background-color: #f9fafb; font-weight: 600; }
    ''',
    
    'valid_elements': '*[*]',
    'extended_valid_elements': 'img[class|src|border=0|alt|title|hspace|vspace|width|height|align|name]',
    'newline_behavior': 'block',
    'remove_trailing_brs': True,
    
    'browser_spellcheck': True,
    'relative_urls': False,
    'remove_script_host': False,
    'convert_urls': True,
    
    
    'images_upload_url': '/tinymce/upload/',
    'automatic_uploads': True,
    'images_reuse_filename': True,
    'file_picker_types': 'image',
    'images_file_types': 'jpg,jpeg,png,gif,webp',
}