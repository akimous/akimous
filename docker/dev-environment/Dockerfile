FROM python:3.8-slim

# debian
RUN set -ex &&\
    apt-get update &&\
    apt-get install -yq --no-install-recommends zsh git curl nano make ca-certificates gnupg2 &&\
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - &&\
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list &&\
    curl -sL https://deb.nodesource.com/setup_13.x | bash - &&\
    apt-get update &&\
    apt-get -yq --no-install-recommends install yarn nodejs zopfli parallel gcc g++

# zsh
ADD .zsh_plugins.txt .zshrc .p10k.zsh /root/
RUN curl -sfL git.io/antibody | sh -s - -b /usr/local/bin &&\
    zsh -c "source ~/.zshrc"

# poetry
RUN set -ex &&\
    pip install --upgrade pip &&\
    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python &&\
    cd ~/.poetry/lib/poetry/_vendor/ &&\
    cp -a py3.7 py3.8 &&\
    cd ~

CMD ["/bin/zsh"]
