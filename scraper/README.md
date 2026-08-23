# Polite Scraper

## Target classification

This Python 3.10+ scraper targets [Books to Scrape](https://books.toscrape.com/), a public practice sandbox built for learning web scraping. The scope is exactly the first three catalogue pages and the 60 books discovered from them. It collects title, URLs, price, availability, rating, description, provenance, and fetch time; that limited collection is appropriate because the site exists specifically for scraping practice.

The one-time request to `https://books.toscrape.com/robots.txt` returned **HTTP 404 (no robots file found)**. A missing robots file is not permission to scrape, so this project remains limited to the assignment's sandbox and scope. I will not reuse this code on another site without checking its rules and terms first.

The Python lane uses `requests`, HTML parsing, schema validation, and the standard JSON/filesystem libraries.

Run from this directory with `python3 src/main.py`. The first run fetches and caches HTML; reruns use the cache. Requests identify themselves, time out after 12 seconds, and wait 500ms after successful live requests. Records are normalized and validated before `output/books.json`; failures go to `output/errors.json`, and every run writes `output/run-report.json`. Use `python3 src/main.py --inject-failure` to verify a deliberately broken URL is isolated.

No browser is needed: the data is already in the HTML sent by the server, so a browser would only add cost. Ethics: use an official API when one exists; never bypass logins, paywalls, or blocks; collect only what you need.
