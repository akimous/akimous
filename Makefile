all: lint | clean static
	cd ui && yarn install
	cd ui && yarn check
	cd ui && yarn run cloc src resources chakuro-agent
	cd ui && yarn run rollup -c

clean:
	mkdir -p dist
	mkdir -p ui_dist
	rm -rf dist/*
	rm -rf ui_dist/*
    
static:
	cp -r ui/src/index.html ui_dist/
	cp -r ui/resources/* ui_dist/
	cp -r ui/node_modules/@fortawesome/fontawesome-free/webfonts ui_dist/
	cp -r ui/node_modules/@fortawesome/fontawesome-free/css/all.min.css ui_dist/webfonts
	cp -r ui/node_modules/devicon/fonts ui_dist/
	touch ui_dist/__init__.py
	for D in ui_dist/*/; do touch $${D}__init__.py; done

lint:
	cd ui && yarn run eslint --ext .html,.js .
	cd ui && yarn run stylelint "resources/*.css src/**/*.html src/**/*.css"
	poetry check

test:
	poetry run python -m pytest -sx

jsdev: | clean static
	cd ui && yarn run rollup -c -w
	
pydev:
	poetry run python akimous --no-browser

upgrade:
	poetry update
	poetry show --outdated
	cd ui && yarn upgrade-interactive --latest
