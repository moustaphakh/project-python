import argparse
from pathlib import Path
import requests
from tqdm import tqdm
import pandas as pd
from colorama import Fore, init
from settings import BASE_URL, INDEX_URL, OUT_CSV_DIR, OUT_IMG_DIR, HEADERS
from utils import ensure_dir, slugify, download_file, absolute_url
from parsers import parse_category_page, parse_book_page, get_soup

init(autoreset=True)


# Defaults
DEFAULT_OUTDIR = Path("outputs")

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape books.toscrape.com")
    parser.add_argument("--categories", type=str, help="Comma-separated list of categories to scrape")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit number of pages per category")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests")
    parser.add_argument("--outdir", type=str, default=str(DEFAULT_OUTDIR), help="Base output directory")
    return parser.parse_args()

def scrape_category_with_limit(session, category_name, category_url, max_pages=None):
    from settings import REQUEST_DELAY_SEC
    all_books = []
    next_page = category_url
    pages_scraped = 0
    while next_page:
        if max_pages is not None and pages_scraped >= max_pages:
            break
        book_urls, next_page = parse_category_page(session, next_page)
        for book_url in tqdm(book_urls, desc=f"{Fore.CYAN}Scraping {category_name}", colour="cyan"):
            try:
                book = parse_book_page(session, book_url, category_name)
                all_books.append(book)
            except Exception as e:
                print(Fore.YELLOW + f"[WARN] Failed {book_url}: {e}")
        pages_scraped += 1
    return all_books

def save_category_csv(category_name, data, outdir=None):
    from settings import OUT_CSV_DIR
    if outdir is None:
        outdir = OUT_CSV_DIR
    ensure_dir(outdir)
    slug = slugify(category_name)
    path = outdir / f"category_{slug}.csv"
    pd.DataFrame(data).to_csv(path, index=False, encoding="utf-8")
    print(Fore.GREEN + f"[DONE] Saved CSV: {path}")
    return path

def download_category_images(session, category_name, data, outdir=None):
    from settings import OUT_IMG_DIR
    if outdir is None:
        outdir = OUT_IMG_DIR
    slug = slugify(category_name)
    folder = outdir / slug
    ensure_dir(folder)
    for row in tqdm(data, desc=f"{Fore.GREEN}Downloading {category_name}", colour="green"):
        url = row.get("image_url", "")
        title = row.get("title", "")
        upc = row.get("upc", "") or "noupc"
        if not url:
            print(Fore.YELLOW + f"[WARN] No image for {title}")
            continue
        try:
            fname = f"{upc}_{slugify(title)}.jpg"
            download_file(session, url, folder / fname)
        except Exception as e:
            print(Fore.YELLOW + f"[WARN] Image failed {title}: {e}")

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

def main():
    import settings
    args = parse_args()

    # Update settings dynamically
    settings.OUT_CSV_DIR = Path(args.outdir) / "csv"
    settings.OUT_IMG_DIR = Path(args.outdir) / "images"
    settings.REQUEST_DELAY_SEC = args.delay

    ensure_dir(settings.OUT_CSV_DIR)
    ensure_dir(settings.OUT_IMG_DIR)

    with requests.Session() as session:
        # Get all categories dynamically
        categories = get_all_categories(session)

        # Filter if requested
        if args.categories:
            selected = [c.strip() for c in args.categories.split(",")]
            categories = {k: v for k, v in categories.items() if k in selected}

        print(Fore.CYAN + f"[INFO] Found {len(categories)} categories: {', '.join(categories.keys())}")

        for cat_name, cat_url in categories.items():
            print(Fore.CYAN + f"[INFO] Starting category: {cat_name}")
            books = scrape_category_with_limit(session, cat_name, cat_url, args.max_pages)
            # pass explicit outdir values this took me so many tries to figure out
            save_category_csv(cat_name, books, settings.OUT_CSV_DIR)
            download_category_images(session, cat_name, books, settings.OUT_IMG_DIR)
            print(Fore.GREEN + f"[DONE] Finished category: {cat_name}\n")

if __name__ == "__main__":
    main()
