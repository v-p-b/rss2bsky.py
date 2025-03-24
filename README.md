RSS to Bluesky - in Python
--------------------------

This is a proof-of-concept implementation for posting RSS/Atom content to Bluesky. Some hacking may be required. Issues and pull requests welcome to improve the system.


## Built with:

* [arrow](https://arrow.readthedocs.io/) - Time handling for humans
* [atproto](https://github.com/MarshalX/atproto) - AT protocol implementation for Python. The API of the library is still unstable, but the version is pinned in requirements.txt
* [fastfeedparser](https://github.com/kagisearch/fastfeedparser) - For feed parsing with a unified API
* [httpx](https://www.python-httpx.org/) - For grabbing remote media


## Features:

* Deduplication: The script queries the target timeline and only posts RSS items that are more recent than the latest top-level post by the handle.
* Filters: Easy to extend code to support filters on RSS contents for simple transformations and limiting cross-posts.
* Minimal rich-text support (links): Rich text is represented in a typed hierarchy in the AT protocol. This script currently performs post-processing on filtered string content of the input feeds to support links as long as they stand as a single line in the text. This definitely needs some improvement.
* Threading for long posts
* Tags
* Image references: Can forward image links from RSS to Bsky

## Usage and configuration

1. Start by installing the required libraries `pip install -r requirements.txt`
2. Copy the configuration file and then edit it `cp config.json.sample config.json`
3. Run the script like `python rss2bsky.py`

The configuration file accepts the configuration of:

* a feed URL
* bsky parameters for a handle, username, and password
  * Handle is like name.bsky.social
  * Username is the email address associated with the account.
  * Password is your password. If you have a literal quote it can be escaped with a backslash like `\"`
* sleep - the amount of time to sleep while running
