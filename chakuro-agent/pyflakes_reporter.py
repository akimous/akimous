from collections import namedtuple

Error = namedtuple('Error', ('msg', 'line', 'ch'))


class PyflakesReporter:
    __slots__ = ['errors']

    def __init__(self):
        self.errors = []

    def unexpectedError(self, filename, msg):
        self.errors.append(Error(msg, 0, 0))

    def syntaxError(self, filename, msg, lineno, offset, text):
        self.errors.append(Error(msg + ' ' + text, lineno, offset))

    def flake(self, msg):
        self.errors.append(Error(msg.message % msg.message_args, msg.lineno, msg.col))
