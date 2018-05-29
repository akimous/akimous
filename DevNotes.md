# Chakuro

## Get started

1. Install the dependencies (only for first time)

   ```yarn install && yarn run build```

2. Start dev server
   ```yarn run dev```

3. Serve via HTTP/2

   1. Enable [allow-insecure-localhost flag](http://peter.sh/experiments/chromium-command-line-switches/#allow-insecure-localhost) on Chrome
   2. `yarn run build`
   3. `yarn run start`

## Build for production

```
yarn upgrade-interactive  -latest
yarn check --integrity
yarn run release
```

## Performance

|              | PWA    | Perf   | BP     | CI       | PSI      | JS(KB)   | BR(KB)  | Transferred |                                   |
| ------------ | ------ | ------ | ------ | -------- | -------- | -------- | ------- | ----------- | --------------------------------- |
| WebComponent | 64     | 31     | 81     | 12350    | 8845     |          |         |             |                                   |
| 1/11         | 73     | 80     | 81     | 3650     | 2825     | 724      | 190     | 588         |                                   |
| 1/21         | 82     | 80     | 88     | 3960     | 2942     | 604      | 158     | 309         |                                   |
| 2/4          | 73     | 80     | 81     | 3890     | 3013     | 620      | 161     | 313         |                                   |
| 2/24         | 73     | 80     | 81     | 3770     | 3069     | 639      | 165     | 291         |                                   |
| 3/7          | 73     | 58     | 88     | 6460     | 4977     | 690      | 172     | 302         |                                   |
| 3/7          | 73     | 65     | 88     | 5520     | 4607     | 717      | 176     | 297         | moved css into js                 |
| 3/17         | 73     | 68     | 88     | 5670     | 3213     | 727      | 180     | 300         |                                   |
| 3/25         | 73     | 65     | 88     | 5830     | 3570     | 725      | 180     | 300         |                                   |
| 4/15         | 73     | 55     | 88     | 6690     | 2958     | 787      | 192     | 315         |                                   |
| 4/20         | 73     | 67     | 88     | 5110     | 3195     | 790      | 192     | 316         | before svelte 2.0                 |
| 4/25         | 73     | 78     | 88     | 3950     | 2637     | 788      | 192     | 316         | don't load xterm on start         |
| 5/26         | 73     | 74     | 88     | 4330     | 2888     | 796      | 193     | 333         | Unused: 45.9%                     |
| 5/29         |        |        |        |          |          | 857      | 200     |             | disable mergeVars in babel-minify |
|              |        |        |        |          |          |          |         |             |                                   |
|              |        |        |        |          |          |          |         |             |                                   |
|              |        |        |        |          |          |          |         |             |                                   |
|              |        |        |        |          |          |          |         |             |                                   |
| **Target**   | **73** | **50** | **85** | **5000** | **3000** | **1000** | **300** | **1000**    |                                   |

