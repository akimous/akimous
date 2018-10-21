# Javascript

## clean

Clean up dist directory.

```bash
mkdir -p dist
rm -rf dist/*
```

## copystatic

Copy index.html and resources to dist directory.

```bash
cp -r src/index.html dist/
cp -r resources/* dist/
cp -r node_modules/@fortawesome/fontawesome-free/webfonts dist/
cp -r node_modules/@fortawesome/fontawesome-free/css/all.min.css dist/webfonts
cp -r node_modules/devicon/fonts dist
```

## lint

Lint javascript.

```bash
eslint --ext .html,.js .
```

## build

Run a full build.

Run task `lint`, `clean`,  `copystatic`

```bash
cloc src resources chakuro-agent
rollup -c
cd dist/
zopfli bundle.js &
brotli bundle.js &
```

## dev

Watch, serve and auto-reload.

Run task `clean`, `copystatic`.

```bash
rollup -c -w
```

## serve

Serve dist

```bash
http-server ./dist -p 5000 -g
```

# Python

## pytest

Run pytest

```bash
cd chakuro-agent
poetry run python -m pytest -sx
```

# Modeling

## download

poetry run python -m modeling.download

```bash
cd chakuro-agent
poetry run python -m modeling.download $1
```

## split

poetry run python -m modeling.split

```bash
cd chakuro-agent
poetry run python -m modeling.split $1
```

## count

poetry run python -m modeling.generate_token_statistics

```bash
cd chakuro-agent
poetry run python -m modeling.generate_token_statistics
```

## extract

extract features in parallel

```bash
cd chakuro-agent
cat $HOME/chakuro-working/training_list.txt $HOME/chakuro-working/testing_list.txt | parallel --progress --eta --memfree 2G --nice 17 poetry run python -m modeling.extract_features {} 1

if [ $1 = 'shutdown' ]
then
	sudo shutdown -h now
fi
```

## train

train the model

```bash
cd chakuro-agent
poetry run python -m modeling.train single
```

## select_features

do feature selection

```bash
cd chakuro-agent
poetry run python -m modeling.select_features
if [ $1 = 'shutdown' ]
then
	sudo shutdown -h now
fi
```

## download_model

```bash
gcloud compute scp $1:~/chakuro-working/model.model ~/chakuro-working/
gcloud compute scp $1:~/chakuro-working/token.xz ~/chakuro-working/
gcloud compute scp $1:~/chakuro-working/bigram.xz ~/chakuro-working/
gcloud compute scp $1:~/chakuro-working/trigram.xz ~/chakuro-working/
```

