from pathlib import Path
import hashlib

DEBUG = False
WORKING_DIR = '/Users/ray/Code/Working/'
working_dir = Path.home() / 'chakuro-working'


def p(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def sha3(x):
    return hashlib.sha3_224(bytes(x, 'utf-8')).hexdigest()

