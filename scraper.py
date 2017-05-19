URL = "https://www.cia.gov/library/publications/the-world-factbook/fields/2080.html"

from lxml import html
import scraperwiki
import requests

def get_page():
    r = requests.get(URL)
    return html.fromstring(r.text)

def clean_fy(value):
    value = value.strip()
    if value == "calendar year": return "1 January"
    if value == "NA": return "Unknown"
    fy_start, fy_end = value.split("-")
    return fy_start
    
def run():
    page = get_page()
    table = page.xpath("//table")[0]
    for row in table.xpath("//tr")[1:]:
        country_code = row.get("id")
        cols = row.xpath("td")
        country_name = cols[0].find("a").text
        fiscal_year = cols[1].text
        scraperwiki.sqlite.save(unique_keys=['code'], data={
            "code": country_code.upper(), 
            "name": country_name,
            "fy_start": clean_fy(fiscal_year)})

run()
