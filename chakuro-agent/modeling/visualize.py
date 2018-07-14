import pickle
import numpy as np
import pandas as pd
import tokenize
from colorama import init
init()
from colorama import Fore as F
from colorama import Back as B
from sklearn.externals import joblib
import sys


show_error = False if len(sys.argv) < 2 else bool(sys.argv[1])

fe = pickle.load(open('/Users/ray/Code/Working/single.pkl', 'rb'))
model = joblib.load('/Users/ray/Code/Working/single.model')
df = fe.dataframe()

file_path = '/Users/ray/Code/Working/keras/keras/optimizers.py'
with open(file_path) as f:
    doc = f.read().splitlines()
with open(file_path, 'rb') as f:
    tokens = list(tokenize.tokenize(f.readline))
train_test_boundary = fe.index[len(fe.index) // 2]

token_i = 0
doc_pos = (0, 0)
df_i = 0
length = len(tokens)
token_selection_start = 0
index_i = 0

completions = list(df.c)
predicted_prob = model.predict_proba(fe.X)[:, 0]


def get_range_from_doc(start, end):
    result = []
    ch = start[1]
    for line in range(max(start[0] - 1, 0), end[0]):
        end_ch = None if line != end[0] - 1 else end[1]
        result.append(doc[line][ch:end_ch])
        ch = 0
    return '\n'.join(result)


def predict_and_color(token):
    global index_i, token_selection_start
    token_selection_end = fe.index[index_i]
    t = fe.tokens[token_selection_start]

    while t.start < token.start:
        index_i += 1
        token_selection_start = token_selection_end
        token_selection_end = fe.index[index_i]
        t = fe.tokens[token_selection_start]

    selections = completions[token_selection_start:token_selection_end]
    if not selections:
        return F.RED
    yp = predicted_prob[token_selection_start:token_selection_end]
    yi = yp.argmax()

    if selections[yi] == token.string:
        return B.RESET + F.GREEN + token.string
    elif token.string not in selections:
        return B.RESET + F.BLUE + token.string
    elif show_error:
        return B.RESET + F.RED + token.string + B.RED + F.WHITE + selections[yi]
    else:
        return B.RESET + F.RED + token.string


while token_i < length:
    token = tokens[token_i]

    if token.start == token.end:
        pass
    elif token.string == '\n':
        pass
    elif token.string.startswith(get_range_from_doc(token.start, token.end)):
        if doc_pos < token.start:
            print(B.RESET + F.BLUE + get_range_from_doc(doc_pos, token.start), end='')
        if token.type in (2, 3, 4, 53, 58):  # (NUMBER, STRING, NEWLINE, OP, NL)
            print(B.RESET + F.RESET + token.string, end='')
        else:
            print(predict_and_color(token), end='')
        doc_pos = token.end

    else:
        print(B.RED + token.string, end='')
    token_i += 1
    # if token_i > 100:
    #     break
