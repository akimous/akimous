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

|              | PWA    | Perf   | BP     | CI       | PSI      | JS(KB)   | BR(KB)  | Transferred |                   |
| ------------ | ------ | ------ | ------ | -------- | -------- | -------- | ------- | ----------- | ----------------- |
| WebComponent | 64     | 31     | 81     | 12350    | 8845     |          |         |             |                   |
| 1/11         | 73     | 80     | 81     | 3650     | 2825     | 724      | 190     | 588         |                   |
| 1/21         | 82     | 80     | 88     | 3960     | 2942     | 604      | 158     | 309         |                   |
| 2/4          | 73     | 80     | 81     | 3890     | 3013     | 620      | 161     | 313         |                   |
| 2/24         | 73     | 80     | 81     | 3770     | 3069     | 639      | 165     | 291         |                   |
| 3/7          | 73     | 58     | 88     | 6460     | 4977     | 690      | 172     | 302         |                   |
| 3/7          | 73     | 65     | 88     | 5520     | 4607     | 717      | 176     | 297         | moved css into js |
|              |        |        |        |          |          |          |         |             |                   |
| **Target**   | **73** | **50** | **85** | **5000** | **3000** | **1000** | **300** | **1000**    |                   |

