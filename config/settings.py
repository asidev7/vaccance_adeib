import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps locales
    'apps.accounts',
    'apps.core',
    'apps.candidatures',
    'apps.enseignants',
    'apps.inscriptions',
    'apps.emploi_du_temps',
    'apps.finances',
    'apps.notes',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.session_active',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Support both DATABASE_URL and individual settings
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    import re
    match = re.match(r'(sqlite|postgres|postgresql)://(?P<user>[^:]*)(:(?P<password>[^@]*))?@(?P<host>[^:/]*)(:(?P<port>\d+))?/(?P<name>.+)', DATABASE_URL)
    if match:
        engine = match.group(1)
        if engine == 'sqlite':
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / match.group('name'),
                }
            }
        else:
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': match.group('name'),
                    'USER': match.group('user'),
                    'PASSWORD': match.group('password') or '',
                    'HOST': match.group('host'),
                    'PORT': match.group('port') or '5432',
                }
            }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Porto-Novo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = '/comite/login/'

# FedaPay
FEDAPAY_API_KEY = config('FEDAPAY_API_KEY', default='')
FEDAPAY_ENVIRONMENT = config('FEDAPAY_ENVIRONMENT', default='sandbox')

# Email (optional)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@adeib.site')

# QR Code tolerance (minutes) — configurable globally, can be overridden per session
QR_TOLERANCE_RETARD_MINUTES = 10

# Jazzmin — Thème Admin ADEIB
JAZZMIN_SETTINGS = {
    "site_title": "ADEIB Vacances Admin",
    "site_header": "ADEIB Vacances",
    "site_brand": "ADEIB Admin",
    "site_logo": "img/logo_adeib.png",
    "login_logo": "img/logo_adeib.png",
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Bienvenue dans l'administration ADEIB Vacances",
    "copyright": "ADEIB — Association pour le Développement de l'Éducation et de l'Insertion au Bénin",
    "search_model": "auth.User",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Accueil", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Voir le site", "url": "/", "new_window": True},
        {"app": "core"},
        {"app": "notes"},
    ],
    "usermenu_links": [
        {"name": "Retour au site", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": [
        "core",
        "accounts",
        "inscriptions",
        "enseignants",
        "emploi_du_temps",
        "candidatures",
        "finances",
        "notes",
    ],
    "custom_links": {},
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "admin.LogEntry": "fas fa-history",
        "accounts.CustomUser": "fas fa-user-tie",
        "core.SessionVacances": "fas fa-calendar-alt",
        "inscriptions.Inscription": "fas fa-user-graduate",
        "inscriptions.Paiement": "fas fa-money-bill-wave",
        "enseignants.Enseignant": "fas fa-chalkboard-teacher",
        "enseignants.Presence": "fas fa-clipboard-check",
        "emploi_du_temps.Matiere": "fas fa-book",
        "emploi_du_temps.Niveau": "fas fa-layer-group",
        "emploi_du_temps.EmploiDuTemps": "fas fa-clock",
        "candidatures.CandidatureEnseignant": "fas fa-file-alt",
        "finances.Depense": "fas fa-shopping-cart",
        "finances.Salaire": "fas fa-wallet",
        "finances.VersementSalaire": "fas fa-hand-holding-usd",
        "notes.Note": "fas fa-star",
        "notes.CoefficientMatiere": "fas fa-sliders-h",
        "notes.BulletinConfig": "fas fa-cogs",
        "notes.BulletinGenere": "fas fa-file-pdf",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark navbar-primary",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
