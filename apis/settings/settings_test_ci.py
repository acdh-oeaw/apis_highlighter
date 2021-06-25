import dj_database_url

from .base import *
import sys


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

APIS_BASE_URI = "https://apis.acdh.oeaw.ac.at/"

ALLOWED_HOSTS = []

SECRET_KEY = (
    "d3j@454545()(/)@zlck/6dsaf*#sdfsaf*#sadflj/6dsfk-11$)d6ixcvjsdfsdf&-u35#ayi"
)
DEBUG = True
DEV_VERSION = False

TEST_RUNNER = "apis_core.testrunners.APISTestRunner"

INSTALLED_APPS = [
    "dal",
    # 'corsheaders',
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "reversion",
    # "reversion_compare",
    "crispy_forms",
    "django_filters",
    "django_tables2",
    "rest_framework",
    "browsing",
    "apis_core.apis_entities",
    "apis_core.apis_metainfo",
    "apis_core.apis_relations",
    "apis_core.apis_vocabularies",
    "apis_core.apis_labels",
    # 'apis_core.apis_vis',
    "rest_framework.authtoken",
    # "drf_yasg",
    "drf_spectacular",
    "guardian",
    "infos",
    "apis_highlighter",
]

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'apis_db_dev',
		'USER': 'apis_user',
		'PASSWORD': 'apis_password',
		'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
		'PORT': '3306',
	}
}

LANGUAGE_CODE = "de"
