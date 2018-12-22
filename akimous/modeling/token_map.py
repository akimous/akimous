from collections import defaultdict
from utils import Timer
import sqlite3


_EMPTY = tuple()


class DirtyMap:
    def __init__(self):
        self.line_to_content = defaultdict(str)

    def is_dirty(self, line, line_content):
        if self.line_to_content[line] is not line_content:
            return True
        return False

    def get_dirty_lines(self, doc):
        result = []
        for line_number, line_content in enumerate(doc):
            if self.is_dirty(line_number, line_content):
                result.append(line_number)
        return result

    def set_clear(self, line, line_content):
        self.line_to_content[line] = line_content


class TokenMap:
    def __init__(self):
        self.line_to_tokens = defaultdict(set)
        self.token_to_lines = defaultdict(set)

    def remove_line(self, line):
        tokens = self.line_to_tokens.pop(line, _EMPTY)
        line_to_remove = {line}
        for token in tokens:
            lines = self.token_to_lines.get(token, _EMPTY)
            if len(lines) == 1:
                del self.token_to_lines[token]
            else:
                lines -= line_to_remove

    def add(self, line, token):
        # with Timer(f'orig.add "{token}"'):
            self.line_to_tokens[line].add(token)
            self.token_to_lines[token].add(line)

    def query(self, token):
        # with Timer(f'orig.query "{token}"'):
        result = self.token_to_lines.get(token, None)
        return result


class PrefixTokenMap:
    def __init__(self):
        self._conn = sqlite3.connect(':memory:')
        self._conn.isolation_level = None
        c = self._conn.cursor()
        c.execute('CREATE TABLE d(t TEXT, l INT)')
        c.execute('CREATE INDEX i1 on d(l)')
        c.execute('CREATE INDEX i2 on d(t, l)')
        c.execute('PRAGMA journal_mode=OFF;').fetchall()

        self.db = c

    def remove_line(self, line):
        self.db.execute('DELETE FROM d WHERE l=?', (line, ))

    def add(self, line, token):
        # with Timer(f'add "{token}"'):
            self.db.execute('INSERT INTO d VALUES(?,?)', (str(token), line))

    def add_many(self, line, tokens):
        with Timer(f'add_many "{tokens}"'):
            self.db.executemany('INSERT INTO d VALUES(?,?)', ((str(token), line) for token in tokens))

    def query_min(self, token):
        with Timer(f'query_min "{token}"'):
            result = self.db.execute('SELECT min(l) FROM d WHERE t=?', (str(token), )).fetchall()[0][0]
        return result

    def query_max(self, token):
        with Timer(f'query_max "{token}"'):
            result = self.db.execute('SELECT max(l) FROM d WHERE t=?', (str(token), )).fetchall()[0][0]
        return result

    def query_min_max(self, token):
        with Timer(f'query_min_max "{token}"'):
            result = self.db.execute('SELECT min(l), max(l) FROM d WHERE t=?', (str(token), )).fetchall()[0]
        return result

    def query_prefix(self, prefix, line):
        # with Timer(f'query_prefix "{prefix}"'):
        result = self.db.execute('SELECT DISTINCT t FROM d WHERE t GLOB ? ORDER BY abs(l-?)',
                                 (f'{prefix}*', line)).fetchall()
        result = [i[0] for i in result]
        return result

    def __del__(self):
        self._conn.close()


if __name__ == '__main__':
    p = PrefixTokenMap()
    p.add(1, 'arstais')
    p.add(3, 'arstais')
    print(p.query_max('arstais'))
    print(p.query_min('arstais'))
    print(p.query_min_max('arstais'))
    print(p.query_prefix('ars', 1))
