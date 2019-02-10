import time

import tqdm

print('中文')

l = list(range(10))

for _ in tqdm.tqdm(l):
    time.sleep(.2)
