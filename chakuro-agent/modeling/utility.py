from pathlib import Path

DEBUG = False
WORKING_DIR = '/Users/ray/Code/Working/'
working_dir = Path.home() / 'chakuro-working'


def p(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
