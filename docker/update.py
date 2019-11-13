from pathlib import Path

tags = {
    'slim': 'python:3.8-slim',
}

template = '''# NOTE: THIS DOCKERFILE IS GENERATED VIA "update.py".
# PLEASE DO NOT EDIT IT DIRECTLY.

FROM {base_image}

RUN set -ex &&\\
    apt-get update &&\\
    apt-get install -yq --no-install-recommends gcc g++ &&\\
    rm -rf /var/lib/apt/lists/* &&\\
    mkdir /home/user

RUN pip install --no-cache-dir akimous

ENV HOME=/home/user
WORKDIR /home/user
EXPOSE 3179
CMD ["akimous"]
'''

for tag, base_image in tags.items():
    Path(f'./{tag}').mkdir(exist_ok=True)
    with open(f'./{tag}/Dockerfile', 'w') as f:
        f.write(template.format(base_image=base_image))
