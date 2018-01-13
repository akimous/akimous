# Chakuro

## Get started

1. Install the dependencies (only for first time)

   ```yarn install && yarn run build```

2. Start dev server
   ```nom run dev```

## Build for production

```
yarn upgrade-interactive
yarn check --integrity
yarn run build
```

## Performance

|              | PWA     | Perf   | BP     | CI       | PSI      | JS(KB)   | BR(KB)  | CSS(KB) |
| ------------ | ------- | ------ | ------ | -------- | -------- | -------- | ------- | ------- |
| WebComponent | 64      | 31     | 81     | 12350    | 8845     |          |         |         |
| 1/11         | 73      | 80     | 81     | 3650     | 2825     | 724      | 190     | 11      |
|              |         |        |        |          |          |          |         |         |
|              |         |        |        |          |          |          |         |         |
|              |         |        |        |          |          |          |         |         |
|              |         |        |        |          |          |          |         |         |
|              |         |        |        |          |          |          |         |         |
|              |         |        |        |          |          |          |         |         |
| **Target**   | **100** | **80** | **85** | **5000** | **3000** | **1000** | **300** | **30**  |

