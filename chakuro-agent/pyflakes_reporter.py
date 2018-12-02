from collections import namedtuple

PyflakesError = namedtuple('PyflakesError', ('msg', 'line', 'ch'))


class PyflakesReporter:
    __slots__ = ['errors']

    def __init__(self):
        self.errors = []

    def unexpectedError(self, filename, msg):
        self.errors.append(PyflakesError(msg, 0, 0))

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.errors.append(PyflakesError(msg + '\n' + text, lineno, offset))

    def flake(self, msg):
        self.errors.append(PyflakesError(msg.message % msg.message_args, msg.lineno, msg.col))

    def clear(self):
        self.errors.clear()
