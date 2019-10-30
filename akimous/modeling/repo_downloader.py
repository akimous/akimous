import itertools
import re
import sqlite3
import time
import traceback
from getpass import getpass

import requests
from git import Repo
from requests.auth import HTTPBasicAuth

from .utility import WORKING_DIR

db = sqlite3.connect('akimous/modeling/temp/repoDatabase.db')

db.execute('drop table repo')
db.execute(
    'create table repo(html_url text, stargazers_count text, updated_at text)')

awesome_list_url = 'https://github.com/vinta/awesome-python/raw/master/README.md'
awesome = requests.get(awesome_list_url)

github_urls = []
non_github_urls = {}  # name: url
RE_LINE_CONTAINS_URL = re.compile('^\*\s\[.*\]\(.*\) - .*$')
for line in awesome.text.splitlines():
    if RE_LINE_CONTAINS_URL.match(line):
        url = line[line.find('(') + 1:line.find(')')]
        if url.startswith('https://github.com/'):
            github_urls.append(url)
        else:
            non_github_urls[line[line.find('[') + 1:line.find(']')]] = url

print(
    f'{len(github_urls)} Github urls, {len(non_github_urls)} non Github urls')

user_name = input('Please input Github account: ')
password = getpass()
auth = HTTPBasicAuth(user_name, password)


def get_github_info(repo_name_or_url):
    if repo_name_or_url is None:
        return
    print(repo_name_or_url)
    try:
        if repo_name_or_url.startswith('https://github.com/'):
            api = repo_name_or_url.replace('https://github.com/',
                                           'https://api.github.com/repos/')
            repo_api_result = requests.get(api, auth=auth)
            json = repo_api_result.json()
        else:
            api = 'https://api.github.com/search/repositories'
            repo_api_result = requests.get(api,
                                           params={
                                               'q': repo_name_or_url,
                                               'per_page': 1
                                           },
                                           auth=auth)
            json = repo_api_result.json()
            if len(json['items']) > 0:
                json = json['items'][0]
        db.execute(
            'insert into repo values(?,?,?)',
            (json['html_url'], json['stargazers_count'], json['updated_at']))
        db.commit()
        rate_limit_remaining = int(
            repo_api_result.headers['X-RateLimit-Remaining'])
        rate_limit_reset_at = time.ctime(
            int(repo_api_result.headers['X-RateLimit-Reset']))
        print(rate_limit_remaining, '\t', rate_limit_reset_at, end='\t')
        if rate_limit_remaining < 7:
            time.sleep(7 - rate_limit_remaining)
    except:
        traceback.print_exc()


# fetch github urls
for a, b in itertools.zip_longest(github_urls, non_github_urls):
    get_github_info(a)
    get_github_info(b)

# clone top repos
top_repos = [
    i[0] for i in db.execute(
        'select * from repo order by cast(stargazers_count as number) desc limit 10'
    )
]
for repo in top_repos:
    repo_name = repo.split('/')[-1]
    print(repo, repo_name)
    Repo.clone_from(repo, WORKING_DIR + repo_name, depth=1)
