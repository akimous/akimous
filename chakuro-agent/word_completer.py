import sqlite3
import wordsegment
from utils import Timer

conn = sqlite3.connect(':memory:')
c = conn.cursor()


def initialize():
    with Timer('Initializing word segment'):
        if not wordsegment.UNIGRAMS:
            wordsegment.load()  # takes 500ms, 100M memory

    with Timer('Initializing SQLite3'):

        c.execute('CREATE TABLE d(p TEXT, w TEXT, f INT, PRIMARY KEY(p, w))')
        # takes 900ms, 15M memory
        c.executemany('INSERT INTO d VALUES (?,?,?)',
                      ((k[:3], k[3:], int(v)) for k, v in wordsegment.UNIGRAMS.items() if len(k) > 3))
        # takes 200ms, 10M memory
        c.execute('CREATE INDEX idx on d(p, f)')
        conn.commit()


initialize()


def search_prefix(s):
    return [
        i[0] for i in c.execute("SELECT p||w FROM d where p=? and w glob ? order by f desc limit 6",
                                (s[:3], f'{s[3:]}*')).fetchall()
    ]
