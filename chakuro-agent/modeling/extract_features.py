import jedi
import time
import tokenize
import token as TOKEN
import pickle
import sys
from tqdm import tqdm
from offline_feature_extractor import OfflineFeatureExtractor
from utility import p, working_dir


def run_file(file_path):
    with open(file_path) as f:
        doc = f.read()
    doc_lines = doc.splitlines()
    line_count = len(doc_lines)
    print(f'File: {file_path}')
    print(f'Line count: {line_count}')

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
    print('Time:', time.time() - start_time)
    print('Successful:', successful_completion_count)
    print('Failed:', failed_completion_count)
    if successful_completion_count > 0:
        print('Naive Accuracy:', sum_of_successful_rates / successful_completion_count)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit(1)
    mode = sys.argv[1]

    if mode not in ('train', 'test', 'both'):
        print('Bad arguments')
        exit(1)

    if mode in ('train', 'both'):
        feature_extractor = OfflineFeatureExtractor()
        with open(working_dir / 'training_list.txt') as f:
            for file in f:
                run_file(file)
        feature_extractor.finalize()
        pickle.dump(feature_extractor, open(working_dir / 'train.pkl', 'wb'), protocol=4)
    if mode in ('test', 'both'):
        feature_extractor = OfflineFeatureExtractor()
        with open(working_dir / 'validation_list.txt') as f:
            for file in f:
                run_file(file)
        feature_extractor.file_path = file
        feature_extractor.finalize()
        pickle.dump(feature_extractor, open(working_dir / 'test.pkl', 'wb'), protocol=4)

    print('Context features:', len(feature_extractor.context_features))
    print('Token features:', len(feature_extractor.token_features))
