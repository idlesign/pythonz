from .sub_paths import PROJECT_DIR_STATE


RAVEN_DSN = ''


RAVEN_CONFIG = {
    'dsn': RAVEN_DSN,
}


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
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': str(PROJECT_DIR_STATE / 'debug.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'root': {
            'level': 'WARNING',
            'handlers': ['sentry'],
            'filters': ['require_debug_false'],
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
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
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}
LOGGERS = LOGGING['loggers']
