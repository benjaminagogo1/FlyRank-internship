# Polite Scraper

## Target classification

This Python 3.10+ scraper targets [Books to Scrape](https://books.toscrape.com/), a public practice sandbox built for learning web scraping. The scope is exactly the first three catalogue pages and the 60 books discovered from them. It collects title, URLs, price, availability, rating, description, provenance, and fetch time; that limited collection is appropriate because the site exists specifically for scraping practice.

The one-time request to `https://books.toscrape.com/robots.txt` returned **HTTP 404 (no robots file found)**. A missing robots file is not permission to scrape, so this project remains limited to the assignment's sandbox and scope. I will not reuse this code on another site without checking its rules and terms first.

The Python lane uses `requests`, a small standard-library HTML parser, Pydantic, and JSON/filesystem libraries. A Pydantic `BookRecord` schema requires all fields, checks types and URL constraints, and routes failures to `errors.json` before storage.

Run from this directory with `./run.sh`. The runner creates a local `.venv` and installs `requirements.txt`, avoiding Debian/Ubuntu's externally-managed system Python restriction. Direct execution is also possible after setup with `.venv/bin/python src/main.py`. The first run fetches and caches HTML; reruns use the cache. Requests identify themselves, time out after 12 seconds, and wait 500ms between live requests. Records are normalized and validated before `output/books.json`; failures go to `output/errors.json`, and every run writes `output/run-report.json`. Use `./run.sh --inject-failure` to verify a deliberately broken URL is isolated.

No browser is needed: the data is already in the HTML sent by the server, so a browser would only add cost. Ethics: use an official API when one exists; never bypass logins, paywalls, or blocks; collect only what you need.

## Record schema

Every stored record has `title`, `product_url`, `price_text`, `availability_text`, `rating_text`, `description` (nullable), `source_page`, `fetched_at`, and numeric `price_gbp`. URLs are absolute HTTPS URLs and records are keyed by canonical product URL, so reruns remain idempotent.

## Evidence

Clean checkpoint: `catalogue_pages=3 discovered=60 unique_urls=60 detail_pages=60`. A rerun reads the cached catalogue/detail HTML and keeps 60 records. With `--inject-failure`, one deliberately fake URL is written to `errors.json`, `failed_pages` becomes 1, and the 60 valid records remain in `books.json`.

Real failure-test report:

```json
{
  "started_at": "2026-08-25T12:46:56.309434+00:00",
  "duration_seconds": 9.13,
  "pages_fetched": 1,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 1,
  "failed_pages": 1,
  "catalogue_pages": 3,
  "discovered": 60,
  "unique_urls": 60
}
```

## Limitation

The cache does not expire automatically, so deleting `cache/` is currently required when a fresh copy of the source pages is needed.
