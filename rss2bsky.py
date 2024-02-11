import feedparser
import atproto
import json
import os

from bs4 import BeautifulSoup

# https://stackoverflow.com/a/66690657
def html_filter(content):
    soup = BeautifulSoup(content, features="html.parser")
    text = ''
    for e in soup.descendants:
        if isinstance(e, str):
            text += e
        elif e.name in ['br',  'p', 'h1', 'h2', 'h3', 'h4', 'tr', 'th']:
            text += '\n'
        elif e.name == 'li':
            text += '\n- '
    return text

def mention_filter(content):
    if content.startswith("@"):
        return ""
    else:
        return content

FILTERS=[ html_filter, mention_filter]


current_path=os.path.dirname(os.path.realpath(__file__))
config=json.load(open(os.path.join(current_path, "config.json"), "r"))

feed=feedparser.parse(config["feed"])

for item in feed["items"]:
    content=item["content"][0]["value"]
    for filter_method in FILTERS:
        content=filter_method(content)
    if len(content)>0:
        print(content)
