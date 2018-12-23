import jedi
import time
import tokenize
import token as TOKEN
import numpy as np
import pandas as pd
import pickle
import random
from tqdm import tqdm
from os import walk, path
from compileall import compile_file
from logzero import logger as log

from .offline_feature_extractor import OfflineFeatureExtractor
from .utility import p, WORKING_DIR

feature_extractor = OfflineFeatureExtractor()


def run_file(file_path):
    with open(file_path) as f:
        doc = f.read()
    doc_lines = doc.splitlines()
    line_count = len(doc_lines)
    print('Line count:', line_count)

    def get_token(line, ch):
        line_tokens = tokens[line]
        for t in line_tokens:
            if t.start[1] <= ch < t.end[1]:
                break
        else:
            return None
        return t

    successful_completion_count = 0
    failed_completion_count = 0
    tokens = [[] for _ in range(line_count + 1)]
    with open(file_path, 'rb') as f:
        for i, token in enumerate(tokenize.tokenize(f.readline)):
            line = token.start[0]
            if line > line_count:
                break
            tokens[line].append(token)

    line, ch = 1, 1  # 1-based
    subdoc = ''
    sum_of_successful_rates = 0.

    start_time = time.time()
    for line in tqdm(range(1, line_count + 1)):
        line_content = doc_lines[line - 1]
        line_length = len(line_content)
        # subdoc += line_content + '\n'
        p('line:', line_content)

        while ch < line_length:
            if not line_content[ch - 1].isalnum():
                ch += 1
                continue

            token = get_token(line, ch)
            if token is None:
                ch += 1
                continue
            elif token.type is not TOKEN.NAME:
                ch = token.end[1] + 1
                continue

            p('>', line, ch, line_content[ch:], end=' ')

            try:
                real_doc_lines = doc_lines[:line]
                real_doc_lines[line - 1] = real_doc_lines[line - 1][:ch]
                full_doc = subdoc + line_content[:ch]
                script = jedi.Script(full_doc, line, ch, file_path)
                completions = script.completions()
            except:
                print(line, ch, line_content)
                break

            accepted_completion = None
            call_signatures = script.call_signatures()
            for comp in completions:
                comp_string = comp.complete
                comp_name = comp.name
                actual_name = line_content[ch - 1:ch + len(comp_string)]

                if len(comp_string) == 0:
                    continue
                if comp_name == actual_name and token.string.endswith(comp_string):
                    accepted_completion = comp_string
                    # add to training dataset
                    feature_extractor.add(token, comp, line_content[:ch], line, ch, full_doc, real_doc_lines, call_signatures)
                else:
                    feature_extractor.add(token, comp, line_content[:ch], line, ch, full_doc, real_doc_lines, call_signatures, False)

            feature_extractor.end_current_completion(accepted_completion)
            if accepted_completion:
                ch += len(accepted_completion) + 1
                successful_completion_count += 1
                sum_of_successful_rates += 1 / len(completions)
                if token.type is not TOKEN.NAME:
                    p(f'\n-----(token is not Name)[{token.string}][{line_content[ch-1]}]', end=' ')
                p(f'(O: {comp_string} {token.string})')
            else:
                token = get_token(line, ch)
                if token is not None:
                    ch = token.end[1]
                else:
                    ch += 1
                failed_completion_count += 1
        ch = 1
        subdoc += line_content + '\n'
    print('time:', time.time() - start_time)
    print('successful:', successful_completion_count)
    print('failed:', failed_completion_count)
    if successful_completion_count > 0:
        print('prediction successful rate:', sum_of_successful_rates / successful_completion_count)


print('Context features:', len(feature_extractor.context_features))
print('Token features:', len(feature_extractor.token_features))

# Run test file
# run_file('test.py')
# feature_extractor.finalize()
# pickle.dump(feature_extractor, open('/Users/ray/Code/Working/good.pkl', 'wb'), protocol=4)
# pd.set_option('display.max_rows', 500000)
# print(feature_extractor.dataframe()[['c', 'y', 'bigram_distance']])

# Run single file
run_file('/Users/ray/Code/Working/keras/keras/optimizers.py')
feature_extractor.finalize()
pickle.dump(feature_extractor, open('/Users/ray/Code/Working/single.pkl', 'wb'), protocol=4)
# pd.set_option('display.max_rows', 500000)
# print(feature_extractor.dataframe()[['c', 'y', 'bigram_distance']])

# Process sanic
# for root, dirs, files in walk('/Users/ray/Code/Working/repos/sanic/sanic'):
#     for i, file_name in enumerate(files):
#         file_path = path.join(root, file_name)
#         print(f'Processing file ({i} / {len(files)}):', file_path)
#         run_file(file_path)

# feature_extractor.finalize()
# pickle.dump(feature_extractor, open('/Users/ray/Code/Working/dataset3.pkl', 'wb'))


# # Process all
# random.seed(0)
# processed_file_count = 0
# file_list = []
# for root, dirs, files in walk(WORKING_DIR + 'repos/'):
#     # skip hidden dirs
#     if '/.' in root or '__' in root:
#         continue
#     if files: 
#         log.info(f'Scanning dir: {root}')
#     for i, file_name in enumerate(files):
#         if not file_name.endswith('.py'):
#             continue
#         file_path = path.join(root, file_name)
#         # skip badly-sized files
#         if not 100 < path.getsize(file_path) < 100_000:
#             continue
#         # skip Python 2 files
#         if not compile_file(file_path, quiet=2):
#             log.warn(f'Skipping file: {file_path}')
#             continue
#         # skip a percentage of files    
#         if random.random() < 0.95:
#             continue
#         file_list.append(file_path)

# for file_path in file_list: 
#     processed_file_count += 1
#     log.info(f'Processing file ({processed_file_count:04}/{len(file_list)}): {file_path}')
#     run_file(file_path)

# feature_extractor.finalize()
# pickle.dump(feature_extractor, open('/Users/ray/Code/Working/dataset4.pkl', 'wb'))
