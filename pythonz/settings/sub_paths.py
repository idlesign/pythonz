import os
from pathlib import Path

BASE_DIR = Path(__file__).absolute().parent.parent

PROJECT_NAME = 'pythonz'
PROJECT_DOMAIN = 'pythonz.net'

PROJECT_DIR_STATE_LOCAL = BASE_DIR.parent / 'state'
LOCAL_RUN = PROJECT_DIR_STATE_LOCAL.exists() or os.environ.get('PYTEST_VERSION')

if LOCAL_RUN:
    PROJECT_DIR_APP = BASE_DIR
    PROJECT_DIR_STATE = PROJECT_DIR_STATE_LOCAL
    PROJECT_DIR_RUN = PROJECT_DIR_STATE_LOCAL
    PROJECT_DIR_CACHE = PROJECT_DIR_STATE_LOCAL

else:
    PROJECT_DIR_APP = Path('/srv') / PROJECT_NAME
    PROJECT_DIR_STATE = Path('/var/lib') / PROJECT_NAME
    PROJECT_DIR_RUN = Path('/run') / PROJECT_NAME
    PROJECT_DIR_CACHE = Path('/var/cache') / PROJECT_NAME


MEDIA_ROOT = f"{PROJECT_DIR_STATE / 'media'}/"
STATIC_ROOT = f"{PROJECT_DIR_STATE / 'static'}/"
