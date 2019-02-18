import sys
from pathlib import Path
from os import walk
from logzero import logger
from compileall import compile_file
import random
from .utility import working_dir


source_dir = working_dir
random.seed(26)
file_list = []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Bad arguments. Should be either tiny, small, medium or large.')
        exit(1)
    mode = sys.argv[1]

    if mode == 'tiny':
        source_dir /= 'keras'
        statistic_file_count, training_file_count, validation_file_count = 10, 1, 1
    elif mode == 'small':
        source_dir /= 'keras'
        statistic_file_count, training_file_count, validation_file_count = 100, 10, 10
    elif mode == 'medium':
        statistic_file_count, training_file_count, validation_file_count = 1000, 100, 100
    elif mode == 'large':
        statistic_file_count, training_file_count, validation_file_count = 10000, 1000, 200
    else:
        print('Bad arguments. Should be either tiny, small, medium or large.')
        exit(1)

    for root, dirs, files in walk(source_dir):
        # skip hidden dirs
        if '/.' in root or '__' in root:
            continue
        if files:
            logger.info(f'Scanning dir: {root}')
        for file_name in files:
            if not file_name.endswith('.py'):
                continue
            file_path = Path(root, file_name)

            # skip badly-sized files
            if not 100 < file_path.stat().st_size < 100_000:
                continue

            # skip Python 2 files
            if not compile_file(file_path, quiet=2):
                logger.warning(f'Skipping file: {file_path}')
                continue

            file_list.append(file_path)

    sample = random.sample(file_list, statistic_file_count + training_file_count + validation_file_count)
    with open(working_dir / 'statistic_list.txt', 'w') as f:
        f.writelines(f'{i}\n' for i in sample[:statistic_file_count])

    training_list_path = working_dir / 'training_list.txt'
    testing_list_path = working_dir / 'testing_list.txt'
    if mode == 'tiny':
        with open(training_list_path, 'w') as f:
            f.writelines([f'{source_dir}/keras/optimizers.py\n'])
        with open(testing_list_path, 'w') as f:
            f.writelines([f'{source_dir}/keras/models.py\n'])
    else:
        with open(training_list_path, 'w') as f:
            f.writelines(f'{i}\n' for i in sample[statistic_file_count:statistic_file_count + training_file_count])
        with open(testing_list_path, 'w') as f:
            f.writelines(f'{i}\n' for i in sample[-validation_file_count:])

    logger.info(f'Written to file {training_list_path}')
    logger.info(f'Written to file {testing_list_path}')
