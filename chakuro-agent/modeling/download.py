import sys
import json
from pathlib import Path
from git import Repo
from .utility import working_dir

REPOS = json.load(open(Path('resources/repo.json')))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    mode = sys.argv[1]
    finished_count = 0

    repos = REPOS
    if mode in ('tiny', 'small'):
        repos = {
            'keras': REPOS['keras']
        }

    for k, v in repos.items():
        print('Cloning', v)
        Repo.clone_from(v, working_dir / k, depth=1)
        finished_count += 1
        if mode in ('tiny', 'small'):
            break
        elif mode == 'medium' and finished_count == 10:
            break
