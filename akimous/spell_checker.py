import json
import re
from collections import namedtuple
from functools import partial
from itertools import chain
from token import COMMENT, NAME, NEWLINE, STRING

from wordsegment import WORDS

from .websocket import register_handler
from .word_completer import is_prefix, wait_until_initialized

SpellingError = namedtuple('SpellingError',
                           ('line', 'ch', 'token', 'highlighted_token'))
Token = namedtuple('Token', ('start', 'string', 'type'))
DummyToken = namedtuple('DummyToken', ('string', ))
dummy = DummyToken('')

KEYWORDS = {'class', 'as'}
AFTER_IMPORT = {'as', 'from'}
STRING_AND_COMMENT = {STRING, COMMENT}
DELIMITER_REGEX = re.compile(r'[_\d]+')
CAMEL_REGEX = re.compile(r'([A-Z][a-z]*)')
NON_WORD = re.compile(r'[\W\d_]+')
MIN_WORD_LENGTH_TO_CHECK = 3

handles = partial(register_handler, '')


@handles('AddToProjectDictionary')
async def add_to_project_dictionary(msg, send, context):
    shared_context = context.shared
    shared_context.spell_checker.project_dictionary.update(msg)
    with open(shared_context.project_dictionary_file, 'w') as f:
        json.dump(
            list(shared_context.spell_checker.project_dictionary),
            f,
            indent=4,
            sort_keys=True)


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
            result = ''.join(
                (result[:index], '<em>', result[index:index + len(w)], '</em>',
                 result[index + len(w):]))
            lowercase_result = result.lower()
            index += 9  # length of <em></em>
    return result


class SpellChecker:
    def __init__(self, context):
        shared_context = context.shared
        shared_context.spell_checker = self
        self.project_dictionary = set()

        # load project dictionary
        if shared_context.project_dictionary_file.exists():
            with open(shared_context.project_dictionary_file, 'r') as f:
                project_dictionary = json.load(f)
            self.project_dictionary.update(project_dictionary)

    async def check_spelling(self, tokens):
        await wait_until_initialized()
        checked = set('')  # both checked tokens and words
        imported_names = set()
        spelling_errors = []

        def import_name(token):
            lower = token.lower()
            if lower in WORDS:
                return
            imported_names.add(lower)
            words = decompose_token(token)
            imported_names.update(words)

        def check_word(word, token):
            if word in checked or len(word) < 4:
                return
            if not word.islower():
                return
            if word in WORDS:
                return
            if word in self.project_dictionary:
                return
            if word in imported_names:
                return
            check_token(
                Token(
                    (token.start[0], token.start[1] + token.string.find(word)),
                    word, NAME))

        def check_token(token):
            if token.type in STRING_AND_COMMENT:
                for w in NON_WORD.split(token.string):
                    check_word(w, token)
                return
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
                if word in self.project_dictionary:
                    is_correct[i] = True
                if word in imported_names:
                    is_correct[i] = True

            checked.add(s)
            checked.update(words)

            if not all(is_correct):
                highlighted_token = highlight_spelling_errors(
                    token.string, words, is_correct)
                spelling_errors.append(
                    SpellingError(*token.start, token.string,
                                  highlighted_token))

        for_ = False
        def_ = False
        import_ = False
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

            if t1s == 'import':
                import_ = True
            elif t0.type == NEWLINE or t0s in AFTER_IMPORT:
                import_ = False

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

            elif t0.type in STRING_AND_COMMENT:
                check_token(t0)

            elif import_:
                import_name(t0s)

        return spelling_errors
