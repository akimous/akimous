from collections import namedtuple
from token import NAME

SpellingError = namedtuple('SpellingError', ('line', 'ch', 'token', 'word'))
DummyToken = namedtuple('DummyToken', ('string', ))
dummy = DummyToken('')


keywords = {'class', 'as'}


def check_spelling(lines_to_tokens):
    checked_tokens = set()
    checked_words = set()

    def check_token(token):
        if token.type != NAME:
            return
        s = token.string
        if len(s) < 4:
            return
        if s in checked_tokens:
            return
        print(token)
        checked_tokens.add(s)

    for line in sorted(lines_to_tokens.keys()):
        tokens = lines_to_tokens[line]
        for_ = False
        def_ = False

        t1, t0 = dummy, dummy

        for token in tokens:
            t1, t0 = t0, token
            t1s, t0s = t1.string, t0.string

            if t1s == 'for':
                for_ = True
            elif t0s == 'in':
                for_ = False

            if t1s == 'def':
                def_ = True
            elif t0s == ':' and t1s == ')':
                def_ = False

            # class xxx:
            if t1s in keywords:
                check_token(t0)

            # def xxx(yyy):
            elif def_:
                check_token(t0)

            # xxx = 123
            elif t0s == '=':
                check_token(t1)

            # for xxx, yyy in something:
            elif for_:
                check_token(t0)


        # break
