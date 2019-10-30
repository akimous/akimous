import hashlib
from itertools import zip_longest
from pathlib import Path

DEBUG = False
working_dir = Path('akimous/modeling/temp')


def p(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def sha3(x):
    return hashlib.sha3_224(bytes(x, 'utf-8')).hexdigest()


def to_columns(lst=[], output_width=140):
    max_length = max(len(i) for i in lst) + 2
    n_columns = output_width // max_length
    items_per_column = len(lst) // n_columns + int(bool(len(lst) % n_columns))
    columns = (lst[i * items_per_column:(i + 1) * items_per_column]
               for i in range(n_columns))
    format_string = ('{:<' + str(max_length) + '}') * n_columns
    result = (format_string.format(*i)
              for i in zip_longest(*columns, fillvalue=''))
    return '\n'.join(result)


def to_key_value_columns(keys, values, output_width=140):
    longest_key = max(len(i) for i in keys)
    format_string = '{:<' + str(longest_key) + '}: {}'
    result = (format_string.format(*i) for i in zip(keys, values))

    return to_columns(list(result), output_width)
