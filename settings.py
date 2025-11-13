from pathlib import Path

BASE_URL = "https://books.toscrape.com/"
INDEX_URL = BASE_URL + "index.html"

REQUEST_DELAY_SEC = 1.0
TIMEOUT_SEC = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

OUT_CSV_DIR = Path("outputs/csv")
OUT_IMG_DIR = Path("outputs/images")

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
