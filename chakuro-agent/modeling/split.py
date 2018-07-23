import sys
from pathlib import Path
from os import walk
from logzero import logger as log
from compileall import compile_file
import random


WORKING_DIR = Path.home() / 'chakuro'
STATISTIC_COUNT = 100
TRAINING_COUNT = 10
VALIDATION_COUNT = 10

random.seed(1)
file_list = []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    mode = sys.argv[1]

    for root, dirs, files in walk(WORKING_DIR):
        # skip hidden dirs
        if '/.' in root or '__' in root:
            continue
        if files:
            log.info(f'Scanning dir: {root}')
        for file_name in files:
            if not file_name.endswith('.py'):
                continue
            file_path = Path(root, file_name)

            # skip badly-sized files
            if not 100 < file_path.stat().st_size < 100_000:
                continue

            # skip Python 2 files
            if not compile_file(file_path, quiet=2):
                log.warn(f'Skipping file: {file_path}')
                continue

            file_list.append(file_path)

    sample = random.sample(file_list, STATISTIC_COUNT + TRAINING_COUNT + VALIDATION_COUNT)
    with open(WORKING_DIR / 'statistic_list.txt', 'w') as f:
        f.writelines(f'{i}\n' for i in sample[:STATISTIC_COUNT])
    with open(WORKING_DIR / 'training_list.txt', 'w') as f:
        f.writelines(f'{i}\n' for i in sample[STATISTIC_COUNT:STATISTIC_COUNT+TRAINING_COUNT])
    with open(WORKING_DIR / 'validation_list.txt', 'w') as f:
        f.writelines(f'{i}\n' for i in sample[-STATISTIC_COUNT:])
