from __future__ import annotations

import argparse, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from html.parser import HTMLParser
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
OUTPUT = ROOT / "output"
BASE = "https://books.toscrape.com/"
START_CATALOGUE = urljoin(BASE, "catalogue/page-1.html")
UA = "FlyRankInternshipA9/1.0 (https://github.com/FlyRank-internship)"

class BookRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    product_url: HttpUrl
    price_text: str = Field(min_length=1)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    description: str | None
    source_page: HttpUrl
    fetched_at: datetime
    price_gbp: float = Field(ge=0)

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.items=[]
    def handle_starttag(self, tag, attrs):
        self.stack.append({"tag": tag, "attrs": dict(attrs), "text": []})
    def handle_endtag(self, tag):
        if not self.stack: return
        frame = self.stack.pop()
        if frame["tag"] != tag: return
        txt=" ".join("".join(frame["text"]).split())
        self.items.append((tag, frame["attrs"], txt, [x["tag"] for x in self.stack] + [tag]))
    def handle_data(self, data):
        if self.stack:
            self.stack[-1]["text"].append(data)

def soup(html):
    p=Parser(); p.feed(html); return p.items

class CatalogueParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.book_links = []
        self.next_link = None
        self._article_depth = 0
        self._next_depth = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get("class", "").split()
        if tag == "article" and "product_pod" in classes:
            self._article_depth += 1
        elif self._article_depth and tag == "article":
            self._article_depth += 1
        if tag == "li" and "next" in classes:
            self._next_depth += 1
        elif self._next_depth and tag == "li":
            self._next_depth += 1
        if tag == "a" and attributes.get("href"):
            if self._article_depth:
                self.book_links.append(attributes["href"])
            elif self._next_depth:
                self.next_link = attributes["href"]

    def handle_endtag(self, tag):
        if tag == "article" and self._article_depth:
            self._article_depth -= 1
        if tag == "li" and self._next_depth:
            self._next_depth -= 1

def catalogue_links(html, page_url):
    parser = CatalogueParser()
    parser.feed(html)
    book_urls = list(dict.fromkeys(urljoin(page_url, href) for href in parser.book_links))
    next_url = urljoin(page_url, parser.next_link) if parser.next_link else None
    return book_urls, next_url

def fetch(url, path, stats, session):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        html = path.read_text(encoding="utf-8")
        stats["cache_hits"] += 1
        print(f"CACHE HIT {path} bytes={len(html.encode('utf-8'))}")
        return html
    for attempt in (1,2):
        stats["pages_fetched"] += 1
        try:
            r=session.get(url, timeout=12)
            if r.status_code == 200:
                r.encoding = "utf-8"
                path.write_text(r.text, encoding="utf-8")
                print(f"FETCH {url} status=200 bytes={len(r.content)}")
                time.sleep(.5)
                return r.text
            # Every live request is separated from the next one, including failures.
            time.sleep(.5)
            if r.status_code >= 500 and attempt == 1: time.sleep(1); continue
            raise RuntimeError(f"HTTP {r.status_code}")
        except requests.RequestException as e:
            time.sleep(.5)
            if attempt == 1: time.sleep(1); continue
            raise RuntimeError(str(e))
    raise RuntimeError("fetch failed")

def text_for(items, tag=None, cls=None):
    for t,a,txt,_ in items:
        if (tag is None or t==tag) and (cls is None or cls in a.get("class", "").split()): return txt
    return None

def repair_mojibake(value):
    if not value or "Â" not in value:
        return value
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value

def remove_repeated_prefix(value):
    if not value or len(value) < 160:
        return value
    marker = value[:100]
    repeated_at = value.find(marker, 100)
    return value[repeated_at:] if repeated_at != -1 else value

def detail(html, url, source):
    it=soup(html)
    title = next((txt for tag, attrs, txt, _ in it if tag == "h1"), None)
    price = next((txt for tag, attrs, txt, _ in it
                  if tag == "p" and "price_color" in attrs.get("class", "").split()), None)
    availability = next((txt for tag, attrs, txt, _ in it
                         if tag == "p" and "availability" in attrs.get("class", "").split()), None)
    rating = next((part for tag, attrs, txt, _ in it
                   if tag == "p" and "star-rating" in attrs.get("class", "").split()
                   for part in attrs.get("class", "").split()
                   if part != "star-rating"), None)
    desc = None
    for i, (tag, attrs, txt, _) in enumerate(it):
        if tag == "div" and attrs.get("id") == "product_description":
            for next_tag, _, next_txt, _ in it[i + 1:]:
                if next_tag == "p":
                    desc = next_txt
                    break
            break
    return {"title":title,"product_url":url,"price_text":repair_mojibake(price),"availability_text":availability,"rating_text":rating,"description":remove_repeated_prefix(desc),"source_page":source,"fetched_at":datetime.now(timezone.utc).isoformat()}

def validate(r):
    m=re.search(r"([0-9]+(?:\.[0-9]+)?)", (r.get("price_text") or "").replace(",", ""))
    if not m: raise ValueError("invalid price")
    r["price_gbp"]=float(m.group(1))
    if not r.get("description"):
        r["description"] = None
    record = BookRecord.model_validate(r)
    if record.product_url.scheme != "https" or record.source_page.scheme != "https":
        raise ValueError("product_url and source_page must use https")
    return record.model_dump(mode="json")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--inject-failure", action="store_true"); ap.add_argument("--discover-only", action="store_true"); ap.add_argument("--detail-only", action="store_true"); args=ap.parse_args()
    start=time.time(); stats={"pages_fetched":0,"cache_hits":0,"valid_records":0,"invalid_records":0,"failed_pages":0}
    CACHE.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True); s=requests.Session(); s.headers["User-Agent"]=UA
    urls=[]; catalogue=[]; source_pages={}; next_url=START_CATALOGUE
    for n in range(1,4):
        page_url=next_url; html=fetch(page_url,CACHE/f"catalogue-page-{n}.html",stats,s); catalogue.append(page_url)
        page_books, next_url = catalogue_links(html, page_url)
        urls.extend(page_books)
        for product_url in page_books:
            source_pages[product_url] = page_url
        if not next_url: break
    discovered = len(urls)
    urls=list(dict.fromkeys(urls))
    unique_discovered = len(urls)
    if args.discover_only:
        print(f"catalogue_pages={len(catalogue)} discovered={discovered} unique_urls={len(urls)}")
        return
    if args.detail_only:
        raw_records = []
        for u in urls:
            try:
                key=re.sub(r"[^a-zA-Z0-9]+", "-", u.rstrip("/").split("/")[-2]) or "page"
                raw_records.append(detail(fetch(u, CACHE/f"{key}.html", stats, s), u, source_pages[u]))
            except Exception as e:
                stats["failed_pages"] += 1
                print(f"ERROR {u}: {e}")
        print(f"detail_pages={len(raw_records)}")
        if raw_records:
            print(json.dumps(raw_records[0], indent=2))
        return
    if args.inject_failure: urls.append(BASE+"catalogue/does-not-exist_9999/index.html")
    records=[]; errors=[]
    for u in urls:
        try:
            key=re.sub(r"[^a-zA-Z0-9]+","-",u.rstrip("/").split("/")[-2]) or "page"
            raw=detail(fetch(u,CACHE/f"{key}.html",stats,s),u,source_pages.get(u, catalogue[0])); records.append(validate(raw))
        except Exception as e: stats["failed_pages"]+=1; errors.append({"product_url":u,"reason":str(e)})
    records={r["product_url"]:r for r in records}; records=list(records.values()); stats["valid_records"]=len(records); stats["invalid_records"]=len(errors)
    (OUTPUT/"books.json").write_text(json.dumps(records,indent=2),encoding="utf-8"); (OUTPUT/"errors.json").write_text(json.dumps(errors,indent=2),encoding="utf-8")
    report={"started_at":datetime.fromtimestamp(start,timezone.utc).isoformat(),"duration_seconds":round(time.time()-start,2),**stats,"catalogue_pages":len(catalogue),"discovered":discovered,"unique_urls":unique_discovered}
    (OUTPUT/"run-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"catalogue_pages={len(catalogue)} discovered={discovered} unique_urls={unique_discovered} detail_pages={len(records)} failed_pages={stats['failed_pages']}")
    if records: print(json.dumps(records[0],indent=2))

if __name__ == "__main__": main()
