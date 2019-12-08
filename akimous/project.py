import json
import sqlite3
from functools import partial
from importlib import resources
from pathlib import Path

from git import InvalidGitRepositoryError, Repo
from logzero import logger

from .config import config, set_config
from .file_finder import find_in_directory, replace_all_in_directory
from .spell_checker import SpellChecker
from .utils import config_directory, merge_dict
from .websocket import register_handler


class PersistentConfig:
    def __init__(self):
        with resources.open_text('akimous.resources',
                                 'default_project_state.json') as f:
            self._default = json.load(f)
        self.db = sqlite3.connect(str(config_directory / 'projects.db3'),
                                  isolation_level=None)
        self.db.execute(
            'CREATE TABLE IF NOT EXISTS c(k TEXT PRIMARY KEY, v TEXT)')

    def __setitem__(self, key, value):
        key = str(key)
        j = json.dumps(value)
        self.db.execute('INSERT OR REPLACE INTO c(k, v) VALUES (?, ?)',
                        (key, j))

    def __getitem__(self, key):
        key = str(key)
        result = self.db.execute('SELECT v FROM c WHERE k=?',
                                 (key, )).fetchall()
        result = json.loads(result[0][0]) if result else {}

        # create default value if not exist
        result = merge_dict(self._default, result)

        # convert paths to tuples
        result['openedFiles'] = list(tuple(i) for i in result['openedFiles'])

        return result

    def close(self):
        self.db.close()


handles = partial(register_handler, 'project')
persistent_state = PersistentConfig()


@handles('OpenProject')
async def open_project(msg, send, context):
    sc = context.shared
    sc.project_root = Path(msg['path']).resolve()

    sc.project_config = persistent_state[sc.project_root]
    sc.project_dictionary_file = sc.project_root / '.akimous' / 'dictionary.json'

    # remove nonexistence files
    opened_files = sc.project_config['openedFiles']
    opened_files = [
        i for i in opened_files if (sc.project_root / Path(*i)).is_file()
    ]
    sc.project_config['openedFiles'] = opened_files

    SpellChecker(context)
    await send('ProjectOpened', {
        'root': sc.project_root.parts,
        'projectState': sc.project_config,
    })
    await set_config({'lastOpenedFolder': str(sc.project_root)}, None, context)

    sc.repo = None


@handles('RequestGitStatusUpdate')
async def request_git_status_update(msg, send, context):
    sc = context.shared
    if not sc.repo:
        try:
            sc.repo = Repo(sc.project_root)
            logger.warning(sc.repo.untracked_files)
        except InvalidGitRepositoryError:
            return
    repo = sc.repo
    try:
        branch = repo.active_branch.name
    except TypeError:
        branch = '(detached)'

    root = context.shared.project_root
    untracked = [Path(i).parts for i in repo.untracked_files]
    changed = [Path(i.a_path).parts for i in repo.index.diff(None)]
    staged = [Path(i.a_path).parts for i in repo.index.diff('HEAD')]
    await send(
        'GitStatusUpdated', {
            'branch': branch,
            'dirty': repo.is_dirty(),
            'untracked': untracked,
            'changed': changed,
            'staged': staged,
        })


@handles('SetProjectState')
async def set_project_state(msg, send, context):
    sc = context.shared
    # save config
    persistent_state[sc.project_root] = merge_dict(sc.project_config, msg)


def save_state(context):
    sc = context.shared
    persistent_state[sc.project_root] = sc.project_config


handles('FindInDirectory')(find_in_directory)
handles('ReplaceAllInDirectory')(replace_all_in_directory)
