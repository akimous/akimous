all: | bootstrap clean static
	cd ui && yarn check
	cd ui && yarn run cloc src resources
	cd ui && yarn run rollup -c
	cd akimous_ui/ && brotli --rm -f *.js *.css *.map *.html
	cd akimous_ui/webfonts && brotli --rm -f *.css
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
	cp -r ui/node_modules/@fortawesome/fontawesome-free/webfonts akimous_ui/
	cp -r ui/node_modules/@fortawesome/fontawesome-free/css/all.min.css akimous_ui/webfonts
	cp -r ui/node_modules/devicon/fonts akimous_ui/
	touch akimous_ui/__init__.py
	for D in akimous_ui/*/; do touch $${D}__init__.py; done

lint:
	cd ui && yarn run cloc src resources
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
	cd ui && yarn upgrade-interactive --latest
