"""
SHL Catalog Scraper — Individual Test Solutions only (type=1).
Paginates through the catalog, collects all product links,
then fetches each product detail page.

Run:  python scripts/scrape_catalog.py
Output: data/catalog.json
"""

import json
import time
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE = "https://www.shl.com"
CATALOG_URL = (
    BASE + "/solutions/products/product-catalog/"
    "?action_doFilteringForm=Search&type=1&start={start}"
)
PAGE_SIZE = 12  # SHL returns 12 items per page; confirmed by inspection
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SHLResearchScraper/1.0; "
        "+https://github.com/shl-intern-submission)"
    )
}
OUTPUT = Path(__file__).parent.parent / "data" / "catalog.json"


def fetch(url: str, retries: int = 3) -> BeautifulSoup:
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            if attempt == retries - 1:
                raise
            print(f"  Retry {attempt+1} for {url}: {e}")
            time.sleep(2 ** attempt)


def parse_catalog_page(soup: BeautifulSoup) -> list[dict]:
    """Extract product rows from a catalog listing page."""
    results = []
    # The catalog renders two tables; we only want Individual Test Solutions.
    target_table = None
    for table in soup.find_all("table"):
        if "Individual Test Solutions" in table.get_text(" ", strip=True):
            target_table = table
            break

    if target_table is None:
        return results

    # Product rows are in the target table; the first row is the header.
    rows = target_table.find_all("tr")[1:]
    for row in rows:
        a = row.find("a")
        if not a:
            continue
        name = a.get_text(strip=True)
        href = a.get("href", "")
        url = href if href.startswith("http") else BASE + href

        # Grab the test-type badges (A/B/K/P/S/C/E columns)
        cells = row.find_all("td")
        remote = False
        adaptive = False
        test_types = []

        for cell in cells:
            text = cell.get_text(strip=True)
            imgs = cell.find_all("img")
            # Some builds use checkmark images instead of text
            if "remote" in cell.get("class", []) or any(
                "remote" in (img.get("alt", "") + img.get("src", "")).lower()
                for img in imgs
            ):
                remote = True
            if "adaptive" in cell.get("class", []) or any(
                "adaptive" in (img.get("alt", "") + img.get("src", "")).lower()
                for img in imgs
            ):
                adaptive = True
            # Test type letters
            if re.fullmatch(r"[ABKPCSE]", text):
                test_types.append(text)

        results.append(
            {
                "name": name,
                "url": url,
                "remote_testing": remote,
                "adaptive_irt": adaptive,
                "test_types": test_types,
            }
        )
    return results


def total_count(soup: BeautifulSoup) -> int:
    """Try to read the total result count from the page."""
    text = soup.get_text()
    m = re.search(r"(\d+)\s+results?\s+found", text, re.I)
    if m:
        return int(m.group(1))
    # Fallback: count the pagination links
    pag = soup.select("a[href*='start=']")
    starts = [int(re.search(r"start=(\d+)", a["href"]).group(1)) for a in pag if re.search(r"start=(\d+)", a.get("href", ""))]
    return max(starts, default=0) + PAGE_SIZE


def parse_detail(soup: BeautifulSoup, url: str) -> dict:
    """Extract description, job levels, languages from a product detail page."""
    detail: dict = {}

    # Description — usually the first substantial <p> under the hero
    desc_el = soup.select_one(".product-catalogue-training-calendar__row p") or \
              soup.select_one("article p") or \
              soup.select_one("main p")
    if desc_el:
        detail["description"] = desc_el.get_text(" ", strip=True)

    text = soup.get_text(" ", strip=True)

    # Job levels
    level_keywords = [
        "Entry-Level", "Graduate", "Mid-Professional",
        "Professional Individual Contributor", "Manager",
        "Director", "Executive", "Supervisor",
        "Front Line Manager", "General Population",
    ]
    found_levels = [l for l in level_keywords if l.lower() in text.lower()]
    detail["job_levels"] = found_levels

    # Languages — look for common language names
    lang_pattern = re.compile(
        r"\b(English[\s\(\w\)]*|French[\s\(\w\)]*|Spanish|German|Portuguese[\s\(\w\)]*|"
        r"Arabic|Chinese[\s\w]*|Japanese|Korean|Dutch|Italian|Polish|Russian|"
        r"Swedish|Danish|Norwegian|Finnish|Turkish|Hindi)\b",
        re.I,
    )
    langs = list(dict.fromkeys(m.group() for m in lang_pattern.finditer(text)))
    detail["languages"] = langs[:20]  # cap

    # Duration
    dur = re.search(r"(\d+)\s*(minutes?|mins?)", text, re.I)
    detail["duration_minutes"] = int(dur.group(1)) if dur else None

    return detail


def scrape() -> list[dict]:
    print("Fetching page 0 to determine total…")
    soup0 = fetch(CATALOG_URL.format(start=0))
    total = total_count(soup0)
    print(f"Estimated total: {total}")

    all_products: dict[str, dict] = {}

    start = 0
    while True:
        print(f"  Catalog page start={start}…")
        soup = soup0 if start == 0 else fetch(CATALOG_URL.format(start=start))
        rows = parse_catalog_page(soup)
        if not rows:
            print("  No rows found — stopping pagination.")
            break
        for p in rows:
            all_products[p["url"]] = p
        if len(rows) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        time.sleep(0.8)

    print(f"\nCollected {len(all_products)} unique products. Fetching detail pages…")

    catalog = []
    for i, (url, product) in enumerate(all_products.items()):
        print(f"  [{i+1}/{len(all_products)}] {product['name'][:60]}")
        try:
            detail_soup = fetch(url, retries=1)
            detail = parse_detail(detail_soup, url)
            product.update(detail)
        except Exception as e:
            print(f"    WARN: {e}")
            # Continue with minimal metadata instead of failing
        catalog.append(product)
        time.sleep(0.3)

    return catalog


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    catalog = scrape()
    OUTPUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\nSaved {len(catalog)} products → {OUTPUT}")


if __name__ == "__main__":
    main()
