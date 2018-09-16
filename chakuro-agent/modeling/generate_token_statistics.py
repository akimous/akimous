import tokenize
import token as token_
from collections import defaultdict
import lzma
import msgpack
from logzero import logger as log
from tqdm import tqdm
from .utility import working_dir

single_token_counter = defaultdict(int)
double_token_counter = defaultdict(int)
triple_token_counter = defaultdict(int)


def run_file(file_path):
    t0, t1, t2 = '', '', ''
    with open(file_path, 'rb') as f:
        for token in tokenize.tokenize(f.readline):
            if token.type not in (token_.STRING, token_.OP, token_.NAME) or len(token.string) > 30:
                continue
            t2, t1, t0 = t1, t0, token.string
            single_token_counter[t0] += 1
            double_token_counter[(t1, t0)] += 1
            triple_token_counter[(t2, t1, t0)] += 1


def serialize(counter, file_name, ratio=.01):
    log.info(f'Serializing {file_name}')
    log.info(f'Original size: {len(counter)}')
    max_count = max(counter.values())
    log.info(f'Max count: {max_count}')
    threshold = max_count * ratio
    counter = {k: v for k, v in counter.items() if v > threshold}
    log.info(f'Filtered size: {len(counter)}')
    with lzma.open(working_dir / file_name, 'wb') as f:
        msgpack.pack(counter, f, use_bin_type=True)


if __name__ == "__main__":
    with open(working_dir / 'statistic_list.txt') as f:
        for file in tqdm(f, disable=False):
            run_file(file.strip())

    serialize(single_token_counter, 'single.msgpack.lzma')
    serialize(double_token_counter, 'double.msgpack.lzma')
    serialize(triple_token_counter, 'triple.msgpack.lzma')
