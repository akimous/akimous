import sys
import time

import tqdm
from logzero import logger

#from matplotlib import pyplot as plt

#%matplotlib inline
logger.debug('中文 █▉▊▋▌▍▎▏')
logger.warning('warn')
logger.error('error')
print(sys.argv)
print('stderr', file=sys.stderr)

echo = input('write something')
#logger.info(echo)

l = list(range(200))

for _ in tqdm.tqdm(l):
    time.sleep(.05)

#plt.plot([1, 2], [3, 4])
