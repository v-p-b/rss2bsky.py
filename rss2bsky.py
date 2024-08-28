import arrow
import feedparser
import json
import os
import logging
import time

from atproto import Client, client_utils
from bs4 import BeautifulSoup


def get_last_bsky(client):
    timeline = client.get_author_feed(config["bsky"]["handle"])
    for titem in timeline.feed:
        # We only care about top-level, non-reply posts
        if titem.reason == None and titem.post.record.reply == None:
            return arrow.get(titem.post.record.created_at)
    # TODO If we only get replies and reposts we are in trouble!


# https://www.docs.bsky.app/docs/advanced-guides/post-richtext
# https://www.spokenlikeageek.com/2023/11/08/posting-to-bluesky-via-the-api-from-php-part-three-links/
# https://atproto.blue/en/latest/atproto_client/utils/text_builder.html
def make_rich(content):
    text_builder = client_utils.TextBuilder()
    for line in content.split("\n"):
        if line.startswith("http"):
            text_builder.link(line + "\n", line.strip())
        else:
            text_builder.text(line + "\n")
    return text_builder


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

def length_filter(content):
    if len(content)>256:
        content=content[0:253]
        content+="..."
    return content

FILTERS = [html_filter, length_filter, mention_filter]

current_path = os.path.dirname(os.path.realpath(__file__))
config = json.load(open(os.path.join(current_path, "config.json"), "r"))

client = Client()
client.login(config["bsky"]["username"], config["bsky"]["password"])

logging.basicConfig(filename="rss2bsky.log", encoding="utf-8", level=logging.INFO)


def run():
    last_bsky = get_last_bsky(client)
    feed = feedparser.parse(config["feed"])

    for item in feed["items"]:
        rss_time = arrow.get(item["published"], [arrow.FORMAT_RFC822, "ddd, DD MMM YYYY HH:mm:ss Z"])
        content = item["content"][0]["value"]
        for filter_method in FILTERS:
            content = filter_method(content)
        if len(content) > 300:
            logging.warning("Post too long :( %s" % (item["link"]))
        if len(content.strip()) > 0:
            rich_text = make_rich(content)
            rich_text.link("\n\nOriginal post", item["link"])
            if rss_time > last_bsky:
                try:
                    client.send_post(rich_text)
                    logging.info("Sent post %s" % (item["link"]))
                except Exception as e:
                    logging.exception("Failed to post %s" % (item["link"]))
            else:
                logging.debug("Not sending %s" % (item["link"]))


while True:
    run()
    time.sleep(config["sleep"])
