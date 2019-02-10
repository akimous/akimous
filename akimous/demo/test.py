import sys
import time

import tqdm
from logzero import logger

logger.info('中文 █▉▊▋▌▍▎▏')
logger.warning('warn')
logger.error('error')

print('stderr', file=sys.stderr)

l = list(range(200))

for _ in tqdm.tqdm(l):
    time.sleep(.05)
