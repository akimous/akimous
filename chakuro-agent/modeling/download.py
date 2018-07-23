import sys
import json
from pathlib import Path
from git import Repo

WORKING_DIR = Path.home() / 'chakuro'
REPOS = json.load(open(Path('../resources/repo.json')))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    mode = sys.argv[1]
    finished_count = 0
    
    for k, v in REPOS.items():
        Repo.clone_from(v, WORKING_DIR / k, depth=1)
        finished_count += 1
        if mode == 'tiny':
            break
        elif mode == 'medium' and finished_count == 10:
            break
