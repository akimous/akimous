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

bootstrap:
	cd ui && yarn install
	poetry install

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
    
	touch akimous_ui/__init__.py
	for D in akimous_ui/*/; do touch $${D}__init__.py; done

lint:
	cd ui && yarn run cloc src resources ../akimous
	cd ui && yarn run eslint --ext .html,.js .
	cd ui && yarn run stylelint "resources/*.css src/**/*.html src/**/*.css"
	poetry check

test:
	poetry run python -m pytest -sx

jsdev: | clean static
	cd ui && yarn run rollup -c -w
	
pydev:
	poetry run python -m akimous --no-browser --verbose

upgrade:
	poetry update
	poetry show --outdated
	cd ui && yarn upgrade
	cd ui && yarn upgrade-interactive --latest

update_docker:
	cd docker && poetry run python update.py