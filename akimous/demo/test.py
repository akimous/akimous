import sys
import time

import tqdm
from logzero import logger

logger.debug('中文 █▉▊▋▌▍▎▏')
logger.warning('warn')
logger.error('error')
print(sys.argv)
print('stderr', file=sys.stderr)

echo = input('write something')
logger.info(echo)

l = list(range(200))

for _ in tqdm.tqdm(l):
    time.sleep(.05)
