DEBUG = True
WORKING_DIR = '/Users/ray/Code/Working/'


def p(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
