all: | bootstrap clean static
	cd ui && yarn check --verify-tree
	cd ui && yarn run rollup -c
	# Firefox does not support brotli on localhost
	cd akimous_ui/ && zopfli *.js *.css *.map *.html && rm *.js *.css *.map *.html
	cd akimous_ui/webfonts && zopfli *.css && rm *.css
	poetry build

install:
	pip uninstall -y akimous
	cd dist && pip install akimous*.whl


### build ###

bootstrap:
	cd ui && yarn install

clean:
	mkdir -p dist
	mkdir -p akimous_ui
	rm -rf dist/*
	rm -rf akimous_ui/*

static:
	cp -r ui/src/index.html akimous_ui/
	cp -r ui/resources/* akimous_ui/
	mkdir -p akimous_ui/webfonts
	cp -r ui/node_modules/@fortawesome/fontawesome-free/webfonts/*.woff2 akimous_ui/webfonts
	cp -r ui/node_modules/@fortawesome/fontawesome-free/css/all.min.css akimous_ui/webfonts
	cp -r ui/node_modules/devicon/fonts/*.woff akimous_ui/fonts

	cp -r ui/node_modules/katex/dist/fonts/*.woff2 akimous_ui/fonts
	cp -r ui/node_modules/katex/dist/katex.mjs akimous_ui/katex.js
	cp -r ui/node_modules/katex/dist/katex.min.css akimous_ui/

	touch akimous_ui/__init__.py
	for D in akimous_ui/*/; do touch $${D}__init__.py; done


### lint and test ###

lint:
	cd ui && yarn run cloc src resources ../akimous
	cd ui && yarn run eslint --ext .html,.js .
	cd ui && yarn run stylelint "resources/*.css" "src/**/*.html" "src/**/*.css"
	poetry check

test: | jstest pytest

pytest:
	poetry run python -m pytest -sx

jstest:
	cd ui && yarn run mocha test/unit_*.js --require esm

singleuitest:
	cd ui && yarn run codeceptjs run --steps ${UNIT}

uitest:
	cd ui && yarn run codeceptjs run --steps ${UNIT}


### development ###

jsdev: | clean static
	cp ui/node_modules/codemirror/mode/python/python.js ui/src/editor/
	cd ui/src/editor && patch < python.js.patch
	cd ui && yarn run rollup -c -w

pydev:
	poetry run python -X dev -m akimous --no-browser --verbose

upgrade:
	poetry update
	poetry show --outdated
	# cd ui && yarn upgrade
	cd ui && yarn upgrade-interactive --latest

fixpoetry:
	poetry cache:clear --all pypi

update_docker:
	cd docker && poetry run python update.py


### model ###

download:
	cd akimous && mkdir -p modeling/temp
	cd akimous && poetry run python -m modeling.download ${N}

sample:
	cd akimous && poetry run python -m modeling.sample ${STATISTICS} ${TRAINING} ${VALIDATION}

statistics:
	cd akimous && poetry run python -m modeling.generate_token_statistics

tinymodel:
	make sample STATISTICS=10 TRAINING=1 VALIDATION=1
	make statistics
