import re
from collections import namedtuple
from itertools import chain
from token import NAME

from wordsegment import WORDS

from word_completer import is_prefix

SpellingError = namedtuple('SpellingError', ('line', 'ch', 'token', 'highlighted_token'))
DummyToken = namedtuple('DummyToken', ('string', ))
dummy = DummyToken('')

KEYWORDS = {'class', 'as'}
DELIMITER_REGEX = re.compile(r'[_\d]+')
CAMEL_REGEX = re.compile(r'([A-Z][a-z]*)')
MIN_WORD_LENGTH_TO_CHECK = 3


def decompose_token(token):
    """
    Split token into words.
    'something' -> ['something']
    'some_variable' -> ['some', 'variable']
    'SomeClass' -> ['some', 'class']
    'SOME_CONSTANT' -> ['some', 'constant']
    :param token: A token
    :return: A list of words in lower case
    """
    parts = DELIMITER_REGEX.split(token)
    if not ''.join(parts).isupper():
        parts = chain.from_iterable(CAMEL_REGEX.split(s) for s in parts)
    return [s.lower() for s in parts if len(s) >= MIN_WORD_LENGTH_TO_CHECK]


def highlight_spelling_errors(token, words, is_correct):
    """
    Wrap bad words in <em> tags.
    :param token: e.g. SomethingWorng
    :param words: e.g. ['something', 'worng']
    :param is_correct: e.g. [True, False]
    :return: e.g. 'Something<em>Worng</em>'
    """
    result = token
    lowercase_result = result.lower()

    index = 0
    for w, i in zip(words, is_correct):
        index = lowercase_result.find(w, index)
        if not i:
            result = ''.join((result[:index], '<em>', result[index:index + len(w)], '</em>', result[index + len(w):]))
            lowercase_result = result.lower()
            index += 9  # length of <em></em>
    return result


def check_spelling(lines_to_tokens):
    checked = set()  # both checked tokens and words
    spelling_errors = []

    def check_token(token):
        if token.type != NAME:
            return
        s = token.string
        if len(s) <= MIN_WORD_LENGTH_TO_CHECK:
            return
        if s in checked:
            return
        words = decompose_token(token.string)
        is_correct = [(i in WORDS) for i in words]

        for i, (word, correct) in enumerate(zip(words, is_correct)):
            if correct:
                continue
            if word in checked or is_prefix(word):
                is_correct[i] = True

        checked.add(s)
        checked.update(words)

        if not all(is_correct):
            highlighted_token = highlight_spelling_errors(token.string, words, is_correct)
            spelling_errors.append(SpellingError(line + 1, token.start[1], token.string, highlighted_token))

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
            if t1s in KEYWORDS:
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

    return spelling_errors
