#!/usr/bin/env python3
"""Polite Books to Scrape pipeline (stdlib + requests)."""
from __future__ import annotations

import argparse, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
OUTPUT = ROOT / "output"
BASE = "https://books.toscrape.com/"
START_CATALOGUE = urljoin(BASE, "catalogue/page-1.html")
UA = "FlyRankInternshipA9/1.0 (https://github.com/FlyRank-internship)"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack=[]; self.items=[]; self.text=[]
    def handle_starttag(self, tag, attrs):
        self.stack.append((tag, dict(attrs))); self.text=[]
    def handle_endtag(self, tag):
        txt=" ".join("".join(self.text).split())
        if txt: self.items.append((tag, dict(self.stack[-1][1]) if self.stack else {}, txt, [x[0] for x in self.stack]))
        if self.stack: self.stack.pop()
    def handle_data(self, data): self.text.append(data)

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
                path.write_text(r.text, encoding="utf-8")
                print(f"FETCH {url} status=200 bytes={len(r.content)}")
                time.sleep(.5)
                return r.text
            if r.status_code >= 500 and attempt == 1: time.sleep(1); continue
            raise RuntimeError(f"HTTP {r.status_code}")
        except requests.RequestException as e:
            if attempt == 1: time.sleep(1); continue
            raise RuntimeError(str(e))
    raise RuntimeError("fetch failed")

def text_for(items, tag=None, cls=None):
    for t,a,txt,_ in items:
        if (tag is None or t==tag) and (cls is None or cls in a.get("class", "").split()): return txt
    return None

def detail(html, url, source):
    it=soup(html); title=text_for(it,"h1")
    price=next((x[2] for x in it if x[0]=="p" and "price_color" in x[1].get("class", "").split()), None)
    availability=next((x[2] for x in it if x[0]=="p" and "availability" in x[1].get("class", "").split()), None)
    rating=next((x[1].get("class", "").split()[-1] for x in it if x[0]=="p" and "star-rating" in x[1].get("class", "").split()), None)
    desc=None
    for i,(t,a,txt,_) in enumerate(it):
        if t=="div" and a.get("id")=="product_description" and i+1<len(it): desc=it[i+1][2]
    return {"title":title,"product_url":url,"price_text":price,"availability_text":availability,"rating_text":rating,"description":desc,"source_page":source,"fetched_at":datetime.now(timezone.utc).isoformat()}

def validate(r):
    required=["title","product_url","price_text","availability_text","rating_text","source_page","fetched_at"]
    missing=[k for k in required if not r.get(k)]
    if missing: raise ValueError("missing fields: "+", ".join(missing))
    m=re.search(r"([0-9]+(?:\.[0-9]+)?)", r["price_text"].replace(",", ""))
    if not m: raise ValueError("invalid price")
    r["price_gbp"]=float(m.group(1)); return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--inject-failure", action="store_true"); ap.add_argument("--discover-only", action="store_true"); args=ap.parse_args()
    start=time.time(); stats={"pages_fetched":0,"cache_hits":0,"valid_records":0,"invalid_records":0,"failed_pages":0}
    CACHE.mkdir(exist_ok=True); OUTPUT.mkdir(exist_ok=True); s=requests.Session(); s.headers["User-Agent"]=UA
    urls=[]; catalogue=[]; next_url=START_CATALOGUE
    for n in range(1,4):
        page_url=next_url; html=fetch(page_url,CACHE/f"catalogue-page-{n}.html",stats,s); catalogue.append(page_url)
        page_books, next_url = catalogue_links(html, page_url)
        urls.extend(page_books)
        if not next_url: break
    discovered = len(urls)
    urls=list(dict.fromkeys(urls))
    if args.discover_only:
        print(f"catalogue_pages={len(catalogue)} discovered={discovered} unique_urls={len(urls)}")
        return
    if args.inject_failure: urls.append(BASE+"catalogue/does-not-exist_9999/index.html")
    records=[]; errors=[]
    for u in urls:
        try:
            key=re.sub(r"[^a-zA-Z0-9]+","-",u.rstrip("/").split("/")[-2]) or "page"
            raw=detail(fetch(u,CACHE/f"{key}.html",stats,s),u,catalogue[min(2,len(catalogue)-1)]); records.append(validate(raw))
        except Exception as e: stats["failed_pages"]+=1; errors.append({"product_url":u,"reason":str(e)})
    records={r["product_url"]:r for r in records}; records=list(records.values()); stats["valid_records"]=len(records); stats["invalid_records"]=len(errors)
    (OUTPUT/"books.json").write_text(json.dumps(records,indent=2),encoding="utf-8"); (OUTPUT/"errors.json").write_text(json.dumps(errors,indent=2),encoding="utf-8")
    report={"started_at":datetime.fromtimestamp(start,timezone.utc).isoformat(),"duration_seconds":round(time.time()-start,2),**stats,"catalogue_pages":len(catalogue),"discovered":discovered,"unique_urls":len(set(urls))}
    (OUTPUT/"run-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(f"catalogue_pages={len(catalogue)} discovered={discovered} unique_urls={len(set(urls))} detail_pages={len(records)}")
    if records: print(json.dumps(records[0],indent=2))

if __name__ == "__main__": main()
