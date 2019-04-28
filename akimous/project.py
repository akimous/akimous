import json
import sqlite3
from functools import partial
from importlib import resources
from pathlib import Path

from logzero import logger

from .file_finder import find_in_directory, replace_all_in_directory
from .spell_checker import SpellChecker
from .utils import config_directory, merge_dict
from .websocket import register_handler


class PersistentConfig:
    def __init__(self):
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
        with resources.open_text('akimous.resources',
                                 'default_project_config.json') as f:
            default = json.load(f)
        key = str(key)
        result = self.db.execute('SELECT v FROM c WHERE k=?',
                                 (key, )).fetchall()
        result = json.loads(result[0][0]) if result else {}

        # create default value if not exist
        result = merge_dict(default, result)

        # convert paths to tuples
        result['openedFiles'] = list(tuple(i) for i in result['openedFiles'])

        return result

    def close(self):
        self.db.close()


handles = partial(register_handler, 'project')
persistent_config = PersistentConfig()


@handles('OpenProject')
async def open_project(msg, send, context):
    sc = context.shared
    sc.project_root = Path(*msg['path']).resolve()

    sc.project_config = persistent_config[sc.project_root]
    sc.project_dictionary_file = sc.project_root / '.akimous' / 'dictionary.json'

    # remove nonexistence files
    opened_files = sc.project_config['openedFiles']
    opened_files = [i for i in opened_files if (sc.project_root / Path(*i)).is_file()]
    sc.project_config['openedFiles'] = opened_files

    await send('ProjectOpened', {
        'root': sc.project_root.parts,
        'projectConfig': sc.project_config
    })
    SpellChecker(context)


@handles('SetProjectConfig')
async def set_project_config(msg, send, context):
    sc = context.shared
    # save config
    persistent_config[sc.project_root] = merge_dict(sc.project_config, msg)


def save_config(context):
    sc = context.shared
    persistent_config[sc.project_root] = sc.project_config


handles('FindInDirectory')(find_in_directory)
handles('ReplaceAllInDirectory')(replace_all_in_directory)
