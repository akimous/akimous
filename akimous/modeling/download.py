import json
import sys
from pathlib import Path

from git import Repo
from logzero import logger

from .utility import working_dir

repositories = json.load(open(Path('akimous/resources/repo.json')))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python -m modeling.download <num_repos>')
        sys.exit(1)

    n_repositories = int(sys.argv[1])
    finished_count = 0

    if n_repositories == 1:
        repositories = {'keras': repositories['keras']}

    for k, v in repositories.items():
        logger.info('Cloning %s', v)
        Repo.clone_from(v, working_dir / k, depth=1)
        finished_count += 1
        if finished_count >= n_repositories:
            break
