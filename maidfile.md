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
cp -r src/index.html resources/* dist/
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
poetry run python -m pytest -s
```

