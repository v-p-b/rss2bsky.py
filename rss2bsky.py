import arrow
import fastfeedparser
import json
import os
import logging
import time
import textwrap
import re

from atproto import Client, client_utils, models
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def get_last_bsky(client):
    if offline:
        return arrow.get(0)
    timeline = client.get_author_feed(config["bsky"]["handle"])
    for titem in timeline.feed:
        # We only care about top-level, non-reply posts
        if titem.reason == None and titem.post.record.reply == None:
            logging.info("Record created %s", str(titem.post.record.created_at))
            return arrow.get(titem.post.record.created_at)
        time.sleep(3)
    # TODO If we only get replies and reposts we are in trouble!


# https://www.docs.bsky.app/docs/advanced-guides/post-richtext
# https://www.spokenlikeageek.com/2023/11/08/posting-to-bluesky-via-the-api-from-php-part-three-links/
# https://atproto.blue/en/latest/atproto_client/utils/text_builder.html
def make_rich(content):
    text_builder = client_utils.TextBuilder()
    for line in content.split("\n"):
        if line.startswith("http"):
            url = line.strip()
            url_obj = urlparse(url)
            text_builder.link("\n %s -> \n" % (url_obj.netloc), url)
        elif line.startswith("RE: http"):
            url = line.split(" ")[1].strip()
            url_obj = urlparse(url)
            text_builder.link("\n>Quoted post<\n", url)
        else:
            tag_split = re.split("(#[a-zA-Z0-9]+)", line)
            for i, t in enumerate(tag_split):
                if i == len(tag_split) - 1:
                    t = t + "\n"
                if t.startswith("#"):
                    text_builder.tag(t, t[1:].strip())
                else:
                    text_builder.text(t)
    return text_builder


def split_message(msg, size=280):
    parts = textwrap.wrap(
        msg, width=size, break_on_hyphens=False, replace_whitespace=False
    )
    return parts


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
    return text.strip()


def mention_filter(content):
    if content.startswith("@") or content.strip().lower().startswith("/cc"):
        return ""
    else:
        return content


def length_filter(content):
    if len(content) > 256:
        content = content[0:253]
        content += "..."
    return content


def frombsky_filter(content):
    if "#frombsky" in content.lower():
        return ""
    else:
        return content


def send_thread(msg, link, client):
    if offline:
        return
    posts = split_message(msg)
    n = len(posts)
    parent = None
    root = None
    logging.info("Sending Thread %s in %d parts" % (link, n))
    for i, p in enumerate(posts):
        logging.debug("Post: '%s'" % p)
        rich_text = make_rich(p)
        rich_text.text(" %d/%d" % (i + 1, n))
        if i == n - 1:
            rich_text.link("\n\nOriginal->", link)
        if i == 0:
            post = client.send_post(text=rich_text)
            root = models.create_strong_ref(post)
        else:
            reply_ref = models.AppBskyFeedPost.ReplyRef(parent=parent, root=root)
            post = client.send_post(text=rich_text, reply_to=reply_ref)
        parent = models.create_strong_ref(post)


# FILTERS = [html_filter, length_filter, mention_filter]
FILTERS = [frombsky_filter, html_filter, mention_filter]

logging.basicConfig(
    format="%(asctime)s %(message)s",
    filename="rss2bsky.log",
    encoding="utf-8",
    level=logging.INFO,
)

current_path = os.path.dirname(os.path.realpath(__file__))
config = json.load(open(os.path.join(current_path, "config.json"), "r"))

client = Client()
offline = False

if config["bsky"]["handle"] == "offline":
    offline = True

if not offline:
    logged_in = False
    backoff = 600
    while not logged_in:
        try:
            client.login(config["bsky"]["username"], config["bsky"]["password"])
            logged_in = True
        except:
            logging.exception("Login exception")
            time.sleep(backoff)
            backoff += 600


def run():
    last_bsky = get_last_bsky(client)
    feed = fastfeedparser.parse(config["feed"])

    for item in feed.entries:
        rss_time = arrow.get(item.published)
        logging.info("RSS Time: %s", str(rss_time))
        content = item.content[0]["value"]
        logging.info("Original Content length: %d" % (len(content)))
        for filter_method in FILTERS:
            content = filter_method(content)
        logging.info("Filtered Content length: %d" % (len(content)))
        if rss_time > last_bsky:
            if len(content) > 280:
                try:
                    send_thread(content, item.link, client)
                except:
                    logging.exception("Exception during thread sending")
                    raise
            elif len(content.strip()) > 0:
                rich_text = make_rich(content)
                logging.info("Rich text length: %d" % (len(str(rich_text))))
                rich_text.link("\n\nOriginal->", item.link)
                try:
                    if not offline:
                        client.send_post(rich_text)
                    logging.info("Sent post %s" % (item.link))
                except Exception as e:
                    logging.exception("Failed to post %s" % (item.link))
        else:
            logging.debug("Not sending %s" % (item.link))


while True:
    run()
    time.sleep(config["sleep"])
