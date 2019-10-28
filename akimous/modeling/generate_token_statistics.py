import lzma
import token as token_
import tokenize
from collections import defaultdict

import msgpack
from logzero import logger
from tqdm import tqdm

from .utility import working_dir

token_counter = defaultdict(int)
bigram_counter = defaultdict(int)
trigram_counter = defaultdict(int)


def run_file(file_path):
    t0, t1, t2 = '', '', ''
    with open(file_path, 'rb') as f:
        for token in tokenize.tokenize(f.readline):
            if token.type not in (token_.STRING, token_.OP,
                                  token_.NAME) or len(token.string) > 30:
                continue
            t2, t1, t0 = t1, t0, token.string
            token_counter[t0] += 1
            bigram_counter[(t1, t0)] += 1
            trigram_counter[(t2, t1, t0)] += 1


def serialize(counter, file_name, ratio=.01):
    logger.info(f'Serializing {file_name}')
    logger.info(f'Original size: {len(counter)}')
    max_count = max(counter.values())
    logger.info(f'Max count: {max_count}')
    threshold = max_count * ratio
    counter = {k: v for k, v in counter.items() if v > threshold}
    logger.info(f'Filtered size: {len(counter)}')
    with lzma.open(working_dir / file_name, 'wb') as f:
        msgpack.pack(counter, f, use_bin_type=True)


if __name__ == "__main__":
    with open(working_dir / 'statistic_list.txt') as f:
        for file in tqdm(f, disable=False):
            run_file(file.strip())

    serialize(token_counter, 'token.xz', ratio=0.00005)
    serialize(bigram_counter, 'bigram.xz', ratio=0.0005)
    serialize(trigram_counter, 'trigram.xz', ratio=0.005)
