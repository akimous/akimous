import sqlite3
from asyncio import sleep
from threading import Thread

import wordsegment

from .utils import Timer

conn = sqlite3.connect(':memory:', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE d(p TEXT, w TEXT, f INT, PRIMARY KEY(p, w))')
initialized = False


def _initialize():
    with Timer('initializing dictionary'):
        global initialized
        # takes 500ms, 100M memory
        wordsegment.load()
        # takes 900ms, 15M memory
        c.executemany('INSERT INTO d VALUES (?,?,?)',
                      ((k[:3], k[3:], int(v))
                       for k, v in wordsegment.UNIGRAMS.items() if len(k) > 3))
        # takes 200ms, 10M memory
        c.execute('CREATE INDEX idx on d(p, f)')
        conn.commit()
        initialized = True


initializer_thread = Thread(target=_initialize)


def initialize(event_loop):
    event_loop.call_later(.01, initializer_thread.start)


def search_prefix(s):
    return [
        i[0] for i in c.execute(
            'SELECT p||w FROM d where p=? and w glob ? order by f desc limit 6',
            (s[:3], f'{s[3:]}*')).fetchall()
    ]


def is_prefix(s):
    return bool(
        c.execute(
            'SELECT 1 FROM d where p=? and w glob ? order by f desc limit 1',
            (s[:3], f'{s[3:]}*')).fetchall())


async def wait_until_initialized():
    while not initialized:
        await sleep(.1)
