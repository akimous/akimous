all: test lint clean | static
	yarn run cloc src resources chakuro-agent
	yarn run rollup -c
	brotli -o dist/bundle.js.br dist/bundle.js

clean:
	mkdir -p dist
	rm -rf dist/*

static:
	cp -r src/index.html dist/
	cp -r resources/* dist/
	cp -r node_modules/@fortawesome/fontawesome-free/webfonts dist/
	cp -r node_modules/@fortawesome/fontawesome-free/css/all.min.css dist/webfonts
	cp -r node_modules/devicon/fonts dist

lint:
	yarn run eslint --ext .html,.js .

test:
	cd chakuro-agent && poetry run python -m pytest -sx

jsdev: | clean static
	yarn run rollup -c -w
	
pydev:
	cd chakuro-agent && poetry run python main.py --no-browser