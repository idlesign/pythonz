import os

from .sub_paths import PROJECT_DIR_STATE

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s (%(module)s) (%(process)d / %(thread)d): %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'pythonz': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'handlers': ['console'],
            'propagate': True,
        },
        'pythonz.apps.management.commands': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

if not os.environ.get('PYTEST_VERSION'):
    # запуск не из автотестов
    LOGGING['handlers']['file'] = {
        'level': 'DEBUG',
        'class': 'logging.FileHandler',
        'filename': f"{PROJECT_DIR_STATE / 'debug.log'}",
        'formatter': 'verbose'
    }

LOGGERS = LOGGING['loggers']
