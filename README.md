# The Polite Scraper

A polite, failure-tolerant web-scraping pipeline built for **FlyRank Internship — Backend Track — Week 5 — Assignment A9**.

The project collects book data from the first three catalogue pages of **Books to Scrape**, discovers the 60 book pages linked from those catalogue pages, extracts and normalizes the data, validates every record, stores valid records as JSON, handles individual page failures without terminating the entire run, and produces a report describing what happened.

The pipeline follows:

```text
Classify → Fetch → Extract → Normalize → Validate → Store → Report
```

The assignment emphasizes that scraping is a pipeline rather than simply copying information from a website. Web content is treated as untrusted input and must be collected politely, normalized, validated, and reported.

---

## Project Status

This README is also being used as the project's implementation guide and progress tracker.

* [ ] Stage 0 — Classify scraping target
* [ ] Stage 1 — Fetch and cache catalogue HTML
* [ ] Stage 2 — Discover three catalogue pages and 60 book URLs
* [ ] Stage 3 — Extract book details
* [ ] Stage 4 — Normalize and validate records
* [ ] Stage 5 — Survive failures and produce run report
* [ ] Stage 6 — Tests, documentation, and publish
* [ ] Bonus — AI rematch

The assignment recommends working through the stages in order, with each stage producing a checkpoint and a meaningful Git commit.

---

# 1. Assignment Scope

## Target

**Books to Scrape**

The target is a public practice sandbox intended for learning web scraping.

## Scope

This scraper will process:

* Catalogue page 1
* Catalogue page 2
* Catalogue page 3
* Every book page discovered from those three catalogue pages
* Exactly 60 unique book URLs

The scraper will **not** crawl the entire catalogue.

The three catalogue pages must be discovered by following the site's own `next` navigation rather than hardcoding the three page URLs or the 60 book URLs.

## Data collected

Each book record will contain:

* title
* product URL
* original price text
* availability text
* rating text
* description
* source catalogue page
* fetch timestamp
* normalized GBP price

---

# 2. Technology Stack

This implementation uses the **Python lane**.

| Purpose           | Technology                                   |
| ----------------- | -------------------------------------------- |
| Runtime           | Python 3.10+                                 |
| HTTP requests     | `requests`                                   |
| HTML parsing      | Beautiful Soup-compatible parser             |
| Schema validation | Pydantic                                     |
| File handling     | Node.js filesystem APIs                      |
| Data format       | JSON                                         |
| Testing           | Node.js test tooling / chosen test framework |
| Version control   | Git                                          |
| Repository        | GitHub                                       |

The assignment permits either JavaScript or Python. This project uses the Python lane throughout.

---

# 3. Architecture

The scraper will be organized as a pipeline with separate responsibilities.

```text
                         ┌─────────────────────┐
                         │   Books to Scrape    │
                         └──────────┬──────────┘
                                    │
                              polite HTTP
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Fetch + Cache     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Catalogue Crawler   │
                         │      Pages 1–3      │
                         └──────────┬──────────┘
                                    │
                              60 unique URLs
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Detail Fetcher    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Raw Extractor     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Normalizer      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Zod Validator     │
                         └──────────┬──────────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                       valid               invalid
                          │                   │
                          ▼                   ▼
                  ┌──────────────┐    ┌──────────────┐
                  │  books.json  │    │ errors.json  │
                  └──────┬───────┘    └──────┬───────┘
                         │                   │
                         └─────────┬─────────┘
                                   ▼
                         ┌─────────────────────┐
                         │  run-report.json   │
                         └─────────────────────┘
```

The important design principle is **separation of concerns**: fetching, crawling, extraction, normalization, validation, storage, and reporting should not become one large function.

---

# 4. Project Structure

The planned structure is:

```text
scraper/
├── src/
│   ├── index.js
│   ├── fetcher.js
│   ├── crawler.js
│   ├── extractor.js
│   ├── normalizer.js
│   ├── validator.js
│   ├── storage.js
│   └── reporter.js
│
├── cache/
│   ├── catalogue/
│   └── books/
│
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
│
├── tests/
│   ├── price.test.js
│   ├── url.test.js
│   ├── description.test.js
│   ├── duplicate.test.js
│   └── malformed.test.js
│
├── .gitignore
├── package.json
└── README.md
```

The exact module names may be adjusted during implementation, but each responsibility should remain clearly separated.

---

# 5. Stage 0 — Classify the Scraping Target

Before writing the scraper, establish that the target is appropriate.

## Tasks

* [ ] Open Books to Scrape and confirm that it is a practice sandbox.
* [ ] Request `https://books.toscrape.com/robots.txt` once.
* [ ] Record the result.
* [ ] Document the target, scope, data collected, and reason for using the site.
* [ ] Add the required statement:

> I will not reuse this code on another site without checking its rules and terms first.

The assignment specifically requires the README to document the target classification and robots check. A missing `robots.txt` must not be interpreted as permission to scrape.

### Planned README information

**Target:** Books to Scrape

**Purpose:** Practice web scraping

**Scope:** First three catalogue pages only

**Expected records:** 60 unique books

**Reason:** Public sandbox designed for scraping practice

**Robots result:** The one-time request returned HTTP 404 (no robots file found). A missing robots file is not permission to scrape.

---

# 6. Stage 1 — Fetch and Cache

The first real request will fetch catalogue page 1.

## Request requirements

Every real request must:

* [ ] Use an identifying User-Agent.
* [ ] Have a timeout.
* [ ] Check the HTTP status.
* [ ] Accept only `200` as a successful page response.
* [ ] Wait at least 500 ms between real requests.
* [ ] Use cached HTML during development.

Example User-Agent:

```text
FlyRankInternship-A9/1.0 (+link-to-repository)
```

The assignment explicitly asks for an honest User-Agent, a timeout, status checking, and local caching.

## Cache

The first request should save:

```text
cache/catalogue/catalogue-page-1.html
```

Subsequent development runs should use the cached copy instead of requesting the website again.

Expected behavior:

```text
First run:
FETCH → status=200 → save cache

Second run:
CACHE HIT → read local HTML
```

The terminal should report the response size without dumping the entire HTML document.

---

# 7. Stage 2 — Discover Catalogue Pages

The crawler will start from catalogue page 1.

## Process

```text
Catalogue page 1
       ↓
Extract book links
       ↓
Extract "next" link
       ↓
Catalogue page 2
       ↓
Extract book links
       ↓
Extract "next" link
       ↓
Catalogue page 3
       ↓
STOP
```

The crawler must:

* [ ] Parse HTML with Cheerio.
* [ ] Extract all book links from each catalogue page.
* [ ] Convert relative URLs to absolute URLs.
* [ ] Follow the catalogue's own `next` link.
* [ ] Stop after page 3.
* [ ] Deduplicate discovered URLs.
* [ ] Avoid hardcoding the 60 book URLs.

Relative URLs must be resolved using URL utilities rather than manual string concatenation.

## Checkpoint

The scraper must eventually report:

```text
catalogue_pages=3
discovered=60
unique_urls=60
```

A second run should produce the same numbers, primarily using the cache.

---

# 8. Stage 3 — Extract Book Details

Each unique book URL will be processed independently.

The raw record must contain the following eight fields:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-06T10:00:00Z"
}
```

These are the eight raw fields specified by the assignment.

## Extraction rules

* [ ] Select elements from the product area rather than making broad page-wide assumptions.
* [ ] Preserve the original price as `price_text`.
* [ ] Preserve the original availability text.
* [ ] Preserve the rating text.
* [ ] Extract the description when available.
* [ ] Store `null` when a description is absent.
* [ ] Store the absolute product URL.
* [ ] Store the catalogue page from which the book was discovered.
* [ ] Record when the page was fetched.

The `source_page` and `fetched_at` fields provide provenance for each record.

## Checkpoint

The program should print:

```text
detail_pages=60
```

and display one complete raw record.

---

# 9. Stage 4 — Normalize and Validate

Raw scraped values will be transformed into values suitable for programmatic use.

## Price normalization

Example:

```text
"£51.77"
      ↓
51.77
```

The final record keeps both:

```json
{
  "price_text": "£51.77",
  "price_gbp": 51.77
}
```

The original scraped value is retained for traceability.

## Canonical identity

The absolute `product_url` will serve as the record's stable identity.

Duplicate URLs must result in only one stored record.

## Schema

The final record will follow a Zod schema covering:

```text
title              string
product_url        valid absolute URL
price_text         string
price_gbp          number
availability_text  string
rating_text        string
description        string | null
source_page        valid absolute URL
fetched_at         valid timestamp
```

## Validation

Every normalized record must pass schema validation before it can enter `books.json`.

Invalid records must instead be written to:

```text
output/errors.json
```

along with the reason for rejection.

The assignment explicitly requires schema validation before storage and separation of invalid records.

---

# 10. Idempotency

The scraper must be safe to run repeatedly.

Expected behavior:

```text
First run  → 60 records
Second run → 60 records
Third run  → 60 records
```

It must never become:

```text
First run  → 60
Second run → 120
```

The canonical product URL will be used to prevent duplicates.

This makes the scraper **idempotent**: running the same job repeatedly produces the same logical result.

## Checkpoint

* [ ] `books.json` contains exactly 60 records.
* [ ] Every record has a unique product URL.
* [ ] Running the scraper again still produces exactly 60 records.

---

# 11. Stage 5 — Failure Handling

A single broken page must not terminate the entire scraping run.

Each detail page will be processed independently.

Example:

```text
Book 1  → success
Book 2  → success
Book 3  → failure
Book 4  → success
...
Book 60 → success
```

The failed page is recorded and skipped while processing continues.

## Retry policy

Retry once for:

* timeout
* server errors (`5xx`)

Do not retry:

* `404`
* `403`

A `404` means the resource does not exist, while a `403` means access was refused. Retrying these indefinitely is neither useful nor polite.

## Failure test

A deliberately fake URL will be added locally to verify failure isolation.

Expected result:

```text
books.json       → 60 good records
failed_pages     → 1
program          → finishes normally
```

The assignment specifically requires this failure scenario to be demonstrated.

---

# 12. Run Report

Every run will produce:

```text
output/run-report.json
```

The report must contain at least:

```json
{
  "started_at": "...",
  "duration_ms": 0,
  "pages_fetched": 0,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

The actual values will be generated by the program.

The report must never pretend that a run was completely successful when pages actually failed.

For example:

```text
valid_records=59
failed_pages=1
```

must remain visible in the report.

The required report fields are specified by the assignment.

---

# 13. Output

The scraper will produce three primary output files.

## `output/books.json`

Contains validated book records.

Expected successful result:

```text
60 unique records
```

## `output/errors.json`

Contains invalid records and/or page-processing failures together with reasons.

## `output/run-report.json`

Contains statistics describing the execution.

The three files answer three different questions:

```text
books.json
→ What valid data did we collect?

errors.json
→ What could not be collected or validated?

run-report.json
→ What happened during the run?
```

---

# 14. Politeness Rules

The scraper will follow these rules:

* [ ] Identify itself with a clear User-Agent.
* [ ] Check `robots.txt`.
* [ ] Limit crawling to the assignment's three catalogue pages.
* [ ] Wait at least 500 ms between real requests.
* [ ] Use request timeouts.
* [ ] Check HTTP status codes.
* [ ] Cache pages during development.
* [ ] Avoid unnecessary requests.
* [ ] Retry only appropriate temporary failures.
* [ ] Never bypass authentication, paywalls, or blocks.
* [ ] Collect only the information required by the assignment.
* [ ] Do not reuse the scraper against another site without checking that site's rules and terms.

The assignment describes these behaviors as part of being a "polite" scraper.

---

# 15. Testing Strategy

The parser should be testable without depending entirely on the live website.

At least five unit tests are required.

## Required tests

* [ ] Price normalization
* [ ] Relative URL → absolute URL
* [ ] Missing description
* [ ] Duplicate URL handling
* [ ] Malformed HTML fixture

Fixtures will be used where appropriate so that parser behavior can be tested repeatedly without making unnecessary network requests.

The assignment requires at least five parser tests covering these cases.

---

# 16. Cache Strategy

Cached HTML is for local development and testing.

Planned structure:

```text
cache/
├── catalogue/
│   ├── catalogue-page-1.html
│   ├── catalogue-page-2.html
│   └── catalogue-page-3.html
│
└── books/
    ├── ...
```

Cache files will not be committed to GitHub.

`.gitignore` should therefore contain:

```text
cache/
```

The public repository should contain code and representative sample output rather than hundreds of cached HTML files.

---

# 17. Installation

## Requirements

* Node.js 20+
* npm
* Git

Check the installed versions:

```bash
node --version
npm --version
git --version
```

## Install dependencies

```bash
npm install
```

The final README should contain one documented command that a stranger can copy and run.

---

# 18. Usage

The final command will be documented here once the implementation is complete.

Planned usage:

```bash
npm start
```

The command should process exactly:

```text
3 catalogue pages
60 unique book URLs
```

and produce:

```text
output/books.json
output/errors.json
output/run-report.json
```

A stranger should be able to clone the repository, install dependencies, run the documented command, and obtain the expected outputs in under five minutes.

---

# 19. Expected Checkpoints

The implementation will be considered on track when the following checkpoints pass.

### Stage 0

```text
Target classification documented
robots.txt result documented
required scope statement present
```

### Stage 1

```text
FETCH on first run
CACHE HIT on second run
status=200
response size reported
```

### Stage 2

```text
catalogue_pages=3
discovered=60
unique_urls=60
```

### Stage 3

```text
detail_pages=60
one complete raw record displayed
all eight raw fields present
```

### Stage 4

```text
books.json = 60 records
price_gbp is numeric
URLs are absolute HTTPS URLs
invalid records go to errors.json
rerun remains at 60 records
```

### Stage 5

```text
one deliberately broken URL
run completes
60 good records survive
failed_pages=1
run-report.json created
```

### Stage 6

```text
public GitHub repository
README complete
sample output included
cache ignored
7+ meaningful commits
stranger can run project in under 5 minutes
```

## These checkpoints directly follow the assignment's staged requirements.

# 20. Sample Run

This section will contain **real output from the completed implementation**.

It should eventually look similar to:

```text
$ npm start

Target: Books to Scrape
Catalogue pages: 3
Discovered URLs: 60
Unique URLs: 60

Detail pages: 60

Valid records: 60
Invalid records: 0
Failed pages: 0

Output:
  output/books.json
  output/errors.json
  output/run-report.json
```

The numbers above are placeholders until the scraper actually produces them.

A real `run-report.json` from a successful run will also be included in the README as evidence, as required by the assignment.

---

# 21. Limitations

The final README will document at least one honest limitation.

Current planned limitation:

> This scraper is intentionally designed for the Books to Scrape practice sandbox and the first three catalogue pages. Its selectors and assumptions are not guaranteed to work against arbitrary websites.

Additional limitations discovered during implementation will be documented here.

---

# 22. Ethics

This project is intended for responsible scraping practice.

The implementation will:

* use an identifiable User-Agent;
* respect request pacing;
* cache pages during development;
* avoid unnecessary traffic;
* check the target's robots information;
* collect only the required public data;
* avoid authentication and paywall bypasses;
* avoid circumventing blocks;
* prefer official APIs when they exist.

The scraper is built for the provided practice sandbox and should not automatically be assumed appropriate for another website.

---

# 23. Optional Extensions

These will only be added after the required assignment is complete.

Possible extensions include:

* [ ] CSV export
* [ ] Change detection between runs
* [ ] Local dashboard
* [ ] Additional HTML selector fixtures
* [ ] Exponential backoff
* [ ] Jitter
* [ ] `Retry-After` handling
* [ ] Structured logs

The assignment explicitly treats these as optional extras rather than core requirements.

---

# 24. Bonus — AI Rematch

After the hand-built scraper is working, an isolated AI-generated implementation may be created.

The AI version will live separately from the hand-built implementation:

```text
ai-version/
```

or in a separate Git branch.

The AI implementation will be evaluated against the same checkpoints:

* Does it discover all 60 books?
* Does it avoid duplicates on rerun?
* Does it handle a broken page?
* Does it validate records?
* Does it follow the politeness rules?
* Does it produce the required report?

The README will eventually contain an **AI vs Me** section covering:

1. What the AI did better.
2. What the AI got wrong or silently skipped.
3. What the prompt failed to specify.
4. What changed after improving the prompt.

The assignment's purpose here is not simply to generate code with AI, but to determine whether an engineer can specify and evaluate an AI-generated implementation.

---

# 25. Final Success Criteria

The project is successful when it can demonstrate all of the following:

```text
3 catalogue pages
        ↓
60 unique book URLs
        ↓
60 detail pages processed
        ↓
raw records extracted
        ↓
values normalized
        ↓
records schema-validated
        ↓
60 unique valid records
        ↓
books.json
        +
errors.json
        +
run-report.json
```

And the scraper must demonstrate:

```text
✓ polite requests
✓ caching
✓ timeout handling
✓ status checking
✓ URL normalization
✓ schema validation
✓ duplicate prevention
✓ failure isolation
✓ run reporting
✓ parser tests
✓ reproducible execution
✓ public GitHub repository
✓ 7+ meaningful commits
```
