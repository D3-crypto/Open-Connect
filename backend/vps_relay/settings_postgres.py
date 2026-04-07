import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'openconnect',
        'USER': 'oc_admin',
        'PASSWORD': 'oc_password',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
