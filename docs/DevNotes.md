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
| 6/3          | 91     | 74     | 88     | 4310     | 2722     | 860      | 201     | 338         | enabled service worker            |
| 7/3          | 73     | 55     | 88     | 4520     | 2992     | 898      | 206     | 357         |                                   |
| 8/24         | 64     | 81     | 88     | 4650     | 3120     | 934      | 212     | 353         | bump dep ver                      |
| 9/24         | 58     | 82     | 87     | 4420     |          | 938      | 213     | 354         | before upgrading babel            |
| 9/25         | 58     | 81     | 87     | 4490     |          | 903      | 208     | 349         | migrate to terser                 |
| **Target**   | **73** | **50** | **85** | **5000** | **3000** | **1000** | **300** | **1000**    |                                   |

## Prediction Accuracy

* `keras/optimizers.py` (12773)

| Date | Evaluate  | Correct  | Wrong | Not Available | Accuracy  | Total     | Features                       | Time    |
| ---- | --------- | -------- | ----- | ------------- | --------- | --------- | ------------------------------ | ------- |
| 7/14 | 55.86     | 802      | 581   | 918           | 57.99     | 34.85     | 39                             | 112     |
| 7/15 | 65.61     | 962      | 421   | 918           | 69.56     | 41.81     | 40, contains in nth line       | 116     |
|      | 67.27     | **984**  | 399   | 918           | **71.15** | 42.76     | 41, contains in nth line lower | 122     |
|      | 67.27     | 984      | 399   | **581**       | 71.15     | **50.10** | exclude single char token      |         |
| 7/16 | 80.78     | **1125** | 258   | 581           | **81.34** | 57.28     | 42, bi-gram                    | 126     |
| 7/17 | 80.63     | 1128     | 255   | 581           | **81.56** | 57.43     | 58, keywords (not good)        | 131     |
|      | **86.37** | 1245     | 138   | 581           | **90.02** | **63.39** | Note 1                         |         |
| 7/18 | 85.89     | 1246     | 137   | 581           | 90.09     | 63.44     | revise blank line before       | 125     |
|      | 86.04     | 1248     | 135   | 581           | **90.24** | **63.54** | 59, contains error             | 125     |
| 7/19 |           |          |       |               |           |           | use StringIO instead of ByteIO | **118** |
| 7/22 | **87.39** | 1255     | 128   | 581           | **90.74** | **63.90** | t2 match                       | 122     |
|      | 87.39     | 1254     | 127   | 581           | 90.82     | 63.95     | t3 match                       | 112     |
|      |           |          |       |               |           |           |                                |         |



| Date | Training Dataset             | Random | Model      | Comment                                                      |
| ---- | ---------------------------- | ------ | ---------- | ------------------------------------------------------------ |
| 8/28 | (70426, 78), 2770 small      | 12.67% | 70.06%     |                                                              |
|      | (1209917, 78), 28737 medium  | 14.15% | **70.79%** | 38min / 1min                                                 |
| 8/29 | (70426, 80), 2770 small      | 12.67% | 70.92%     | **starts with _, __**                                        |
| 8/31 | (70426, 82), 2770 small      | 12.67% | 70.48%     | indent, indent_delta                                         |
|      | (70426, 83), 2770 small      | 12.67% | 69.55%     | line_number                                                  |
| 9/12 | (143186, 151), 3243 small    | 15.15% | 73.65%     | **bugs fixed, added popular builtins**                       |
|      | (143186, 151), 3243 small    | 15.15% | 72.75%     | return MAX when t1/2/3 not found                             |
|      | (1529931, 151), 29209 medium | 15.51% | **71.90%** |                                                              |
| 9/13 | (1529931, 151), 29209 medium | 15.51% | **72.05%** | return MAX when t2/3 not found                               |
| 9/14 | (143186, 152), 3243 small    | 15.15% | 72.45%     | trigram                                                      |
|      | (143186, 160), 3243 small    | 15.15% | 72.15%     | last line ends with                                          |
| 9/16 | (143186, 162), 3243 small    | 15.15% | 73.57%     | **first token (partial) ratio**                              |
|      | (143186, 162), 3243 small    | 15.15% | 73.31%     | don't return -1 when on the same token (rolled back)         |
|      | (143186, 164), 3243 small    | 15.15% | 73.63%     | **last line first token partial ratio**                      |
|      | (143186, 165), 3243 small    | 15.15% | 74.08%     | **last n lines first token partial ratio**                   |
|      | (143186, 166), 3243 small    | 15.15% | 74.09%     | **left char is dot**                                         |
|      | (143186, 166), 3243 small    | 15.15% | 73.89%     | first token ratio should consider STRING (dict key)          |
|      | (143186, 166), 3243 small    | 15.15% | 73.68%     | if token.start[1] <= ch < token.end[1]: return -2 (rolled back) |
|      | (143186, 168), 3243 small    | 15.15% | 74.08%     | **all token ratio**                                          |
| 9/18 | (143186, 171), 3243 small    | 15.15% | 75.16%     | **token, bigram, trigram frequencies**                       |
|      | (143186, 171), 3243 small    | 15.15% | 74.89%     | normalized frequencies                                       |
| 9/19 | (1529932, 171), 29209 medium | 15.51% | **75.07%** | normalized=True                                              |
|      | (1529932, 171), 29209        | 15.51% | **75.13%** | normalized=False                                             |
|      | (1529932, 174), 29209        | 15.51% | 74.83%     | normalized=Both                                              |
| 9/20 | (1529932, 171), 29209        |        | **76.47%** | RandomForest, min_split=1                                    |
| 10/2 | (1529932, 154), 29209        | 15.51% | **75.20%** | XGB, function signature                                      |
|      |                              |        | **76.85%** | RF, min_split=1                                              |

* float distance
* first token in line is (identifier, keyword, def, if, self)

## Plan

1. Integrate zero character prediction (70%)
2. Improve accuracy (80%-90%)
3. Incompletable / full statement completion (50%)



## Expected Training Time

* Tiny: 5 mins
* Small: 1 hour
* Medium: 10 hours
* Large: 1 day (4 cores)

## Model Building Procedure

* download
* split
* extract_feature
* train
* visualize
* https://github.com/channelcat/sanic
* https://github.com/kaxap/arl/blob/master/README-Python.md

```bash
gcloud compute ssh red8012@tw-1
curl https://raw.githubusercontent.com/red8012/ServerSetupScript/master/GCE_Ubuntu_1804.sh | bash
exit
gcloud compute ssh red8012@tw-1
git clone git@gitlab.com:red8012/chakuro.git
chakuro/chakuro-agent/
git checkout poetry
poetry install
screen

poetry run python -m modeling.download small
poetry run python -m modeling.split small
cat $HOME/chakuro-working/training_list.txt $HOME/chakuro-working/testing_list.txt | parallel --progress --eta --memfree 2G --nice 17 poetry run python -m modeling.extract_features {} 1
poetry run python -m modeling.train single
# poetry run python visualize.py
gcloud compute scp red8012@tw-1:~/chakuro-working/model.model ~/chakuro-working/gce


cat $HOME/chakuro-working/training_list.txt $HOME/chakuro-working/testing_list.txt | parallel --progress --eta --nice 17 python -m modeling.extract_features {} 1
python -m modeling.extract_features /Users/ray/chakuro-working/keras/examples/mnist_siamese.py 1
```
