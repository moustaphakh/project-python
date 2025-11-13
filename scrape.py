import argparse
from pathlib import Path
from utils import ensure_dir, slugify
from parsers import parse_category_page, parse_book_page, get_soup
from settings import OUT_CSV_DIR, OUT_IMG_DIR
import requests
import pandas as pd
from tqdm import tqdm
from colorama import Fore, init

init(autoreset=True)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", type=str)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--outdir", type=str, default="outputs")
    return parser.parse_args()

def main():
    args = parse_args()
    global OUT_CSV_DIR, OUT_IMG_DIR
    OUT_CSV_DIR = Path(args.outdir) / "csv"
    OUT_IMG_DIR = Path(args.outdir) / "images"
    ensure_dir(OUT_CSV_DIR)
    ensure_dir(OUT_IMG_DIR)

    with requests.Session() as session:
        # Example: scraping Travel category for testing
        category_name = "Travel"
        category_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"
        books, _ = parse_category_page(session, category_url)
        data = []
        for book_url in tqdm(books, desc=f"Scraping {category_name}", colour="cyan"):
            book_data = parse_book_page(session, book_url, category_name)
            data.append(book_data)

        df = pd.DataFrame(data)
        df.to_csv(OUT_CSV_DIR / f"category_{slugify(category_name)}.csv", index=False)

if __name__ == "__main__":
    main()
