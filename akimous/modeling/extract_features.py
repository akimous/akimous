import logging
import pickle
import sys
import time
import token as TOKEN
import tokenize

import logzero
from logzero import logger
from tqdm import tqdm

from .completion_engine import CompletionEngine
from .offline_feature_extractor import OfflineFeatureExtractor
from .utility import p, sha3, working_dir


def run_file(file_path,
             feature_extractor,
             silent=False,
             zero_length_prediction=False):
    with open(file_path) as f:
        doc = f.read()
    engine = CompletionEngine(file_path, '')
    doc_lines = doc.splitlines()
    line_count = len(doc_lines)
    print(f'Processing file: {file_path}')
    logger.info(f'Line count: {line_count}')

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
    sum_of_successful_rates = 0.

    start_time = time.time()
    for line in tqdm(range(1, line_count + 1), disable=silent):
        line_content = doc_lines[line - 1]
        line_length = len(line_content)
        p('line:', line_content)

        while ch < line_length:
            should_skip = not line_content[ch - 1].isalnum()
            if zero_length_prediction and line_content[ch - 1] == '.':
                should_skip = False
            if should_skip:
                ch += 1
                continue
            token = get_token(
                line,
                ch)  # don't + 1 on ch, or it will clip short (2ch) tokens
            if token is None:
                ch += 1
                continue
            elif token.type is not TOKEN.NAME:
                ch = token.end[1] + 1
                continue
            # p('>', line, ch, line_content[ch:], end=' ')
            try:
                real_doc_lines = doc_lines[:line]
                real_doc_lines[line - 1] = real_doc_lines[line - 1][:ch]
                completions = engine.complete(line, ch, line_content[:ch])
            except Exception as e:
                print(line, ch, line_content)
                logger.exception(e)
                break

            accepted_completion = None
            call_signatures = engine.jedi.call_signatures()

            deduplication_set = set()
            for comp in completions:
                comp_string = comp.complete
                comp_name = comp.name
                if comp_name in deduplication_set:
                    continue
                deduplication_set.add(comp_name)
                # actual_name = line_content[ch - 1:ch + len(comp_string)]
                if len(comp_string) == 0:
                    continue
                # if comp_name == actual_name and token.string == comp_name:
                if comp_name == token.string:
                    accepted_completion = comp_string
                    # add to training dataset
                    feature_extractor.add(token, comp, line_content[:ch], line,
                                          ch, real_doc_lines, call_signatures)
                else:
                    feature_extractor.add(token, comp, line_content[:ch], line,
                                          ch, real_doc_lines, call_signatures,
                                          False)

            feature_extractor.end_current_completion(accepted_completion)
            if accepted_completion:
                ch += len(accepted_completion) + 1
                successful_completion_count += 1
                sum_of_successful_rates += 1 / len(completions)
                if token.type is not TOKEN.NAME:
                    p(f'\n-----(token is not Name)[{token.string}][{line_content[ch-1]}]',
                      end=' ')
                p(f'(O: {token.string})')
            else:
                token = get_token(line, ch)
                if token is not None:
                    ch = token.end[1]
                else:
                    ch += 1
                failed_completion_count += 1
        ch = 1
        engine.update(line, line_content)
    logger.info(f'Time: {time.time() - start_time}')
    logger.info(f'Successful: {successful_completion_count}')
    logger.info(f'Failed: {failed_completion_count}')
    if successful_completion_count > 0:
        logger.info(
            f'Naive Accuracy: {sum_of_successful_rates / successful_completion_count}'
        )


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python -m akimous.modeling.extract_features '
              '<path/to/a/python/file.py> [zero_length_prediction]\n\n'
              '(zero_length_prediction default to True)')
        sys.exit(1)
    target = sys.argv[1]
    zero_length_prediction = False
    if len(sys.argv) < 3 or bool(int(sys.argv[2])):
        zero_length_prediction = True

    logzero.loglevel(logging.WARNING)
    feature_extractor = OfflineFeatureExtractor()
    file = target.strip()
    run_file(file,
             feature_extractor,
             silent=True,
             zero_length_prediction=zero_length_prediction)
    feature_extractor.finalize()
    extraction_path = working_dir / 'extraction'
    extraction_path.mkdir(exist_ok=True)
    pickle.dump(feature_extractor,
                open(extraction_path / f'{sha3(file)}.pkl', 'wb'),
                protocol=4)
    logger.info(f'Context features: {len(feature_extractor.context_features)}')
    logger.info(
        f'Token features: {len(feature_extractor.completion_features)}')
