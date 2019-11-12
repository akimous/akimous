all: | bootstrap clean static
	cd ui && yarn check --verify-tree
	cd ui && yarn run rollup -c
	# Firefox does not support brotli on localhost
	cd akimous_ui/ && zopfli *.js *.css *.map *.html && rm *.js *.css *.map *.html
	cd akimous_ui/webfonts && zopfli *.css && rm *.css
	poetry build
	poetry install

install:
	pip uninstall -y akimous
	cd dist && pip install akimous*.whl

staging: | all
	poetry config repositories.testpypi https://test.pypi.org/legacy/
	poetry publish --repository testpypi

publish:
	poetry publish


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
	cd ui && yarn run cloc --exclude-dir=testOutput,temp src resources ../akimous
	cd ui && yarn run eslint --ext .html,.js .
	cd ui && yarn run stylelint "resources/*.css" "src/**/*.html" "src/**/*.css"
	poetry check

test: | jstest pytest uitest

pytest:
	poetry run python -m pytest -sx --ignore akimous/modeling/temp

jstest:
	cd ui && yarn run mocha test/unit_*.js --require esm

singleuitest:
	cd ui && yarn run codeceptjs run --steps ${UNIT}

uitest:
	rm ~/Library/Application\ Support/akimous/* || true
	rm ~/.config/akimous/* || true
	poetry run python -m akimous --no-browser --port 3178 &
	sleep 7
	make singleuitest UNIT=test/prepare_test.js
	make singleuitest UNIT=test/panel_FileTree_test.js
	make singleuitest UNIT=test/menu_File_test.js
	make singleuitest UNIT=test/editor_RealtimeFormatter_test.js
	pkill -9 -f "akimous --no-browser"
	sleep 3


### development ###

jsdev: | clean static
	cp ui/node_modules/codemirror/mode/python/python.js ui/src/editor/
	cd ui/src/editor && patch < python.js.patch
	cd ui && yarn run rollup -c -w

pydev:
	poetry run python -X dev -m akimous --no-browser --verbose --port 3178

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
	mkdir -p akimous/modeling/temp
	poetry run python -m akimous.modeling.download ${N}

sample:
	poetry run python -m akimous.modeling.sample ${STATISTICS} ${TRAINING} ${VALIDATION}

statistics:
	poetry run python -m akimous.modeling.generate_token_statistics
    
features:
	cat akimous/modeling/temp/training_list.txt akimous/modeling/temp/testing_list.txt > akimous/modeling/temp/list.txt
	parallel --eta --progress --memfree 2G --nice 17 -a akimous/modeling/temp/list.txt poetry run python -m akimous.modeling.extract_features {} 1

xgboost:
	nice -n 19 poetry run python -m akimous.modeling.train

model1:
	make sample STATISTICS=10 TRAINING=1 VALIDATION=1
	make statistics
	make features

model10:
	make sample STATISTICS=100 TRAINING=10 VALIDATION=10
	make statistics
	make features

model100:
	make sample STATISTICS=10000 TRAINING=1000 VALIDATION=100
	make statistics
	make features

visualize:
	poetry run python -m akimous.modeling.visualize ${FILE} ${SHOW_ERROR} ${KNOWN_INITIAL}
