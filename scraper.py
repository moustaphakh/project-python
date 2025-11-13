import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)

BASE_URL = "https://books.toscrape.com/"
INDEX_URL = urljoin(BASE_URL, "index.html")

OUT_CSV_DIR = Path("outputs/csv")
OUT_IMG_DIR = Path("outputs/images")

REQUEST_DELAY_SEC = 1.0     # polite delay between requests
TIMEOUT_SEC = 20
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def ensure_dir(path: Path):
    """Create directories safely (no error if already exists)."""
    path.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    """Make file-safe names (no spaces or special chars)."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"

def get_soup(session, url: str) -> BeautifulSoup:
    """Download & parse HTML safely, returning BeautifulSoup object."""
    time.sleep(REQUEST_DELAY_SEC)
    resp = session.get(url, headers=HEADERS, timeout=TIMEOUT_SEC)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")

def text_or_none(node) -> str:
    """Extract text safely."""
    return node.get_text(strip=True) if node else ""

def to_float_price(text: str) -> float:
    """Convert '£51.77' → 51.77"""
    if not text:
        return float("nan")
    try:
        return float(re.sub(r"[^0-9.]", "", text))
    except ValueError:
        return float("nan")

def parse_stock_count(text: str) -> int:
    """Extract stock count from 'In stock (22 available)' → 22"""
    m = re.search(r"\((\d+)\s+available\)", text)
    return int(m.group(1)) if m else 0

def absolute_url(base: str, rel: str) -> str:
    """Join relative URL with base safely."""
    return urljoin(base, rel)

def parse_book_page(session, book_url: str, category_name: str) -> dict:
    """Parse a single book’s page and extract all details."""
    soup = get_soup(session, book_url)

    title = text_or_none(soup.select_one("div.product_main h1"))
    price_text = text_or_none(soup.select_one("p.price_color"))
    price = to_float_price(price_text)
    stock_text = text_or_none(soup.select_one("p.instock.availability"))
    stock_count = parse_stock_count(stock_text)

    rating_tag = soup.select_one("p.star-rating")
    rating_word = ""
    rating_num = None
    if rating_tag:
        for c in rating_tag.get("class", []):
            if c in RATING_MAP:
                rating_word = c
                rating_num = RATING_MAP[c]
                break

    
    img_tag = soup.select_one("div.item.active img")
    img_rel = img_tag["src"] if img_tag else ""
    image_url = absolute_url(book_url, img_rel)

   
    upc = ""
    table = soup.select_one("table.table-striped")
    if table:
        for tr in table.select("tr"):
            key = text_or_none(tr.select_one("th"))
            val = text_or_none(tr.select_one("td"))
            if key == "UPC":
                upc = val

    return {
        "title": title,
        "price": price,
        "price_raw": price_text,
        "stock": stock_count,
        "stock_raw": stock_text,
        "rating_word": rating_word,
        "rating": rating_num,
        "product_url": book_url,
        "image_url": image_url,
        "upc": upc,
        "category": category_name
    }

def parse_category_page(session, category_url: str):
    """Extract all book URLs on one category page."""
    soup = get_soup(session, category_url)
    books = [absolute_url(category_url, a["href"])
             for a in soup.select("article.product_pod h3 a")]

    next_link = soup.select_one("li.next a")
    next_page = absolute_url(category_url, next_link["href"]) if next_link else None
    return books, next_page

def scrape_category(session, category_name: str, category_url: str):
    """Scrape all books in one category (with tqdm progress bar)."""
    all_books = []
    next_page = category_url
    while next_page:
        book_urls, next_page = parse_category_page(session, next_page)
        for book_url in tqdm(book_urls, desc=f"{Fore.CYAN}Scraping {category_name}", colour="cyan"):
            try:
                book = parse_book_page(session, book_url, category_name)
                all_books.append(book)
            except Exception as e:
                print(Fore.YELLOW + f"[WARN] Failed {book_url}: {e}")
    return all_books

def get_all_categories(session):
    """Collect all category names and their URLs."""
    soup = get_soup(session, INDEX_URL)
    cats = {}
    for a in soup.select("ul.nav.nav-list li a"):
        name = a.get_text(strip=True)
        if name.lower() == "books":
            continue
        cats[name] = absolute_url(INDEX_URL, a["href"])
    return cats

def save_category_csv(category_name, data):
    """Save scraped data into a CSV file per category."""
    ensure_dir(OUT_CSV_DIR)
    slug = slugify(category_name)
    path = OUT_CSV_DIR / f"category_{slug}.csv"
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding="utf-8")
    print(Fore.GREEN + f"[DONE] Saved CSV: {path}")
    return path

def download_category_images(session, category_name, data):
    """Download all book images in a category with progress bar."""
    slug = slugify(category_name)
    folder = OUT_IMG_DIR / slug
    ensure_dir(folder)
    for row in tqdm(data, desc=f"{Fore.GREEN}Downloading {category_name}", colour="green"):
        url = row.get("image_url", "")
        title = row.get("title", "")
        upc = row.get("upc", "") or "noupc"
        if not url:
            print(Fore.YELLOW + f"[WARN] No image for {title}")
            continue
        try:
            resp = session.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT_SEC)
            resp.raise_for_status()
            fname = f"{upc}_{slugify(title)}.jpg"
            with open(folder / fname, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
        except Exception as e:
            print(Fore.YELLOW + f"[WARN] Image failed {title}: {e}")


def main():
    ensure_dir(OUT_CSV_DIR)
    ensure_dir(OUT_IMG_DIR)

    with requests.Session() as session:
        categories = get_all_categories(session)
        print(Fore.CYAN + f"[INFO] Found {len(categories)} categories.")

        for cat_name, cat_url in categories.items():
            print(Fore.CYAN + f"[INFO] Starting category: {cat_name}")
            try:
                books = scrape_category(session, cat_name, cat_url)
                save_category_csv(cat_name, books)
                download_category_images(session, cat_name, books)
                print(Fore.GREEN + f"[DONE] Finished category: {cat_name}\n")
            except Exception as e:
                print(Fore.RED + f"[ERROR] Skipping {cat_name}: {e}")

if __name__ == "__main__":
    main()
