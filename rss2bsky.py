import arrow
import feedparser
import json
import os
import pprint

pp = pprint.PrettyPrinter(indent=4)

from atproto import Client
from bs4 import BeautifulSoup


def get_last_bsky(client):
    timeline = client.get_author_feed(config["bsky"]["handle"])
    for titem in timeline.feed:
        # print(titem.post.record.text, titem.reason == None, titem.post.record.reply == None, titem.post.record.created_at)
        # We only care about top-level, non-reply posts
        if titem.reason == None and titem.post.record.reply == None:
            return arrow.get(titem.post.record.created_at)
    # TODO If we only get replies and reposts we are in trouble!


# https://stackoverflow.com/a/66690657
def html_filter(content):
    soup = BeautifulSoup(content, features="html.parser")
    text = ""
    for e in soup.descendants:
        if isinstance(e, str):
            text += e
        elif e.name in ["br", "p", "h1", "h2", "h3", "h4", "tr", "th"]:
            text += "\n"
        elif e.name == "li":
            text += "\n- "
    return text


def mention_filter(content):
    if content.startswith("@"):
        return ""
    else:
        return content


FILTERS = [html_filter, mention_filter]

current_path = os.path.dirname(os.path.realpath(__file__))
config = json.load(open(os.path.join(current_path, "config.json"), "r"))

client = Client()
client.login(config["bsky"]["username"], config["bsky"]["password"])

last_bsky = get_last_bsky(client)
feed = feedparser.parse(config["feed"])

for item in feed["items"]:
    rss_time = arrow.get(item["published"])
    content = item["content"][0]["value"]
    for filter_method in FILTERS:
        content = filter_method(content)
    if len(content) > 0:
        print(content)
        print(rss_time, last_bsky)
        if rss_time > last_bsky:
            print("Post this")
        else:
            print("Don't post")
