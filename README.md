# Akimous

[![PyPI version](https://badge.fury.io/py/akimous.svg)](https://pypi.python.org/pypi/akimous/) [![PyPI pyversions](https://img.shields.io/pypi/pyversions/akimous.svg)](https://pypi.python.org/pypi/akimous/) [![CircleCI](https://circleci.com/gh/akimous/akimous/tree/master.svg?style=svg)](https://circleci.com/gh/akimous/akimous/tree/master)

Akimous is a Python IDE with unique features boosting developers' productivity.

### Features

* Machine-learning-assisted/NLP-assisted context-aware auto completion
* Beautifully rendered function documentation
* Layered keyboard control (a more intuitive key binding than vim and Emacs)
* Real-time code formatter
* Interactive console (integration with IPython kernel)

<img src="https://raw.githubusercontent.com/akimous/akimous/master/images/screenshot.png" alt="Screenshot" style="max-width:100%">

For more information and documentation, visit the official website.

## Installation

### Prerequisite

* Python 3.7 or 3.8
* C/C++ compiler (required by some dependencies during installation)
* A modern browser

### Installing From PyPI

The recommended way for installing Akimous is through PyPI.

```sh
pip install -U akimous
```

### Starting Application

Start it in the terminal. The browser should be automatically opened.

```sh
akimous
```

* To see available arguments, do `akimous --help`.

### Using Docker Image

If you have difficulty installing, or you are running in a cloud environment, try the prebuilt docker image.

```sh
docker run --mount type=bind,source=$HOME,target=/home/user -p 127.0.0.1:3179:3179 -it red8012/akimous akimous
```

## Commands

Start the app by typing in the terminal (the browser will automatically open if available): 

```sh
akimous
```

#### Options

* `--help`: show help message and exit.
* `--host HOST`: specify the host for Akimous server to listen on. (default to 0.0.0.0 if inside docker, otherwise 127.0.0.1)
* `--port PORT`: The port number for Akimous server to listen on. (default=3179)
* `--no-browser`: Do not open the IDE in a browser after startup.
* `--verbose`: Print extra debug messages.

## Development

Make sure you have recent version of the following build dependencies installed.

* Node (12+)
* Python (3.7+)
* [Poetry](https://poetry.eustace.io)
* [Yarn](https://yarnpkg.com/)
* Make
* [Zopfli](https://github.com/google/zopfli)
* [Parallel](https://www.gnu.org/software/parallel/)

Run the following commands according to your need.

```sh
make # build everything
make test # run tests
make lint # run linters
make install # (re)install the package
```

Running `make` will install all Python and Javascript dependencies listed in `pyproject.toml` and `ui/package.json` automatically.

## Contributing

This program is at pre-alpha stage. Please do report issues if you run into some problems. Contributions of any kind are welcome, including feature requests or pull requests (can be as small as correcting spelling errors) . 

## License

[BSD-3-Clause](LICENSE)

## Links

* [Official website](https://akimous.com)
* [PyPI](https://pypi.org/project/akimous/)
* [Docker Hub](https://hub.docker.com/r/red8012/akimous)

