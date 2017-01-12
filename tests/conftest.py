import sys
from os.path import dirname, abspath

PROJECT_PATH = dirname(dirname(abspath(__file__)))

sys.path = [dirname(PROJECT_PATH), PROJECT_PATH] + sys.path
