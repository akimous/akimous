FROM python:3.8-slim

# debian
RUN set -ex &&\
    apt-get update &&\
    apt-get install -yq --no-install-recommends zsh git curl nano make ca-certificates gnupg2 &&\
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - &&\
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list &&\
    curl -sL https://deb.nodesource.com/setup_13.x | bash - &&\
    apt-get update &&\
    apt-get -yq --no-install-recommends install yarn nodejs zopfli parallel gcc g++ wget

# chrome
# https://github.com/GoogleChrome/puppeteer/blob/master/docs/troubleshooting.md#running-puppeteer-in-docker
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -yq google-chrome-unstable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
      --no-install-recommends \
    && groupadd -r user && useradd -r -g user -G audio,video user \
    && mkdir -p /home/user/Downloads \
    && chown -R user:user /home/user \
    && chmod -R 777 /usr/local/bin

USER user

# zsh
ADD .zsh_plugins.txt .zshrc .p10k.zsh /home/user/
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
