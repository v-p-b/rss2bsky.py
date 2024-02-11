RSS to Bluesky - in Python
--------------------------

This is a proof-of-concept implementation for posting RSS/Atom content to Bluesky. Some hacking may be required. 


Built with:

* [arrow](https://arrow.readthedocs.io/) - Time handling for humans
* [atproto](https://github.com/MarshalX/atproto) - AT protocol implementation for Python. The API of the library is still unstable, but the version is pinned in requirements.txt
* [feedparser](https://feedparser.readthedocs.io/) - For feed parsing


Features:

* Deduplication: The script queries the target timeline and only posts RSS items that are more recent than the latest top-level post by the handle
* Filters: Easy to extend code to support filters on RSS contents for simple transformations and limiting cross-posts
* Minimal rich-text support (links): Rich text is represented in a typed hierarchy in the AT protocol. This script currently performs post-processing on filtered string content of the input feeds to support links as long as they stand as a single line in the text. This definitely needs some improvement

