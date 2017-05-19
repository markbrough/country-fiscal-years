URL = "https://www.cia.gov/library/publications/the-world-factbook/fields/2080.html"

from lxml import html
import scraperwiki
import requests
import shutil
from git import Repo
from os.path import join
from os import environ, remove
from glob import glob
import unicodecsv

output_dir = "output"
data_dir = join(output_dir, "data")

def get_page():
    r = requests.get(URL)
    return html.fromstring(r.text)

def clean_fy(value):
    value = value.strip()
    if value == "calendar year": return "01 January"
    if value == "NA": return "Unknown"
    fy_start, fy_end = value.split("-")
    day, month  = fy_start.strip().split(" ")
    # Samoa says "June 1" - so switch around
    if len(month)<3: day, month = month, day
    if len(day)==1:
        return "0{} {}".format(day, month)
    return fy_start.strip()

def init_git_repo():
    shutil.rmtree(output_dir, ignore_errors=True)
    git = Repo.init(output_dir).git
    git.remote('add', 'origin', 'https://{}@github.com/markbrough/country-fiscal-years.git'.format(environ.get('MORPH_GH_API_KEY')))
    try:
        git.pull('origin', 'update')
        git.checkout(b='update')
    except:
        git.pull('origin', 'gh-pages')
        git.checkout(b='update')
    for to_remove in glob(join(data_dir, '*.csv')):
        remove(to_remove)

def push_to_github():
    url = 'https://api.github.com/repos/markbrough/country-fiscal-years/pulls'
    git = Repo.init(output_dir).git
    git.add('.')
    git.config('user.email', environ.get('MORPH_GH_EMAIL'))
    git.config('user.name', environ.get('MORPH_GH_USERNAME'))
    git.commit(m='Update')
    git.push('origin', 'update')
    payload = {
        'title': 'Merge in latest changes',
        'body': 'This is an auto- pull request.',
        'head': 'update',
        'base': 'gh-pages',
    }
    r = requests.post(url, json=payload, auth=(environ.get('MORPH_GH_USERNAME'), environ.get('MORPH_GH_API_KEY')))
    shutil.rmtree(output_dir, ignore_errors=True)

def run():
    page = get_page()
    table = page.xpath("//table")[0]

    init_git_repo()
    with open(join(data_dir, 'countries_fiscal_years.csv'), 'w') as f:
        writer = unicodecsv.DictWriter(f, fieldnames=["code","name","fy_start"], 
                                quoting=unicodecsv.QUOTE_ALL)
        writer.writeheader()
        for row in table.xpath("//tr")[1:]:
            country_code = row.get("id")
            cols = row.xpath("td")
            country_name = cols[0].find("a").text
            fiscal_year = cols[1].text
            data = {"code": country_code.upper(), 
                    "name": country_name,
                    "fy_start": clean_fy(fiscal_year)}
            scraperwiki.sqlite.save(unique_keys=['code'], data=data)
            writer.writerow(data)
    push_to_github()

run()
