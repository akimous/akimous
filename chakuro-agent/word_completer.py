import sqlite3
import wordsegment

from utils import Timer


with Timer('Initializing word completer'):
    if not wordsegment.UNIGRAMS:
        wordsegment.load()

    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute('CREATE TABLE d(p TEXT, w TEXT, f INT, PRIMARY KEY(p, w))')
    c.executemany('INSERT INTO d VALUES (?,?,?)',
                  ((k[:3], k[3:], int(v)) for k, v in wordsegment.UNIGRAMS.items() if len(k) > 3))
    c.execute('CREATE INDEX idx on d(p, f)')
    conn.commit()


def search_prefix(s):
    return [
        i[0] for i in c.execute("SELECT p||w FROM d where p=? and w glob ? order by f desc limit 6",
                                (s[:3], f'{s[3:]}*')).fetchall()
    ]
