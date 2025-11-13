import time
import re
from bs4 import BeautifulSoup
from settings import HEADERS, REQUEST_DELAY_SEC, TIMEOUT_SEC, RATING_MAP
from utils import absolute_url, slugify

def get_soup(session, url: str) -> BeautifulSoup:
    time.sleep(REQUEST_DELAY_SEC)
    resp = session.get(url, headers=HEADERS, timeout=TIMEOUT_SEC)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")

def text_or_none(node):
    return node.get_text(strip=True) if node else ""

def to_float_price(text: str) -> float:
    if not text:
        return float("nan")
    try:
        return float(re.sub(r"[^0-9.]", "", text))
    except ValueError:
        return float("nan")

def parse_stock_count(text: str) -> int:
    m = re.search(r"\((\d+)\s+available\)", text)
    return int(m.group(1)) if m else 0

def parse_book_page(session, book_url: str, category_name: str) -> dict:
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
    soup = get_soup(session, category_url)
    books = [absolute_url(category_url, a["href"])
             for a in soup.select("article.product_pod h3 a")]
    next_link = soup.select_one("li.next a")
    next_page = absolute_url(category_url, next_link["href"]) if next_link else None
    return books, next_page
