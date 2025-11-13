# Book Scraper

A simple Python scraper for [books.toscrape.com](https://books.toscrape.com/).  
It collects book details (title, price, stock, rating, UPC, image, etc.)  
and saves them into CSV files, with images downloaded locally.

---

## Setup

```bash
pip install -r requirements.txt
```
## How to use
```bash
python scrape.py
```
## Specific scraping
```bash
python scrape.py --categories Travel,Poetry
```
## Limit number of pages
```bash
python scrape.py --categories Travel --max-pages 1
```
## Change request delay
```bash
python scrape.py --delay 2
```

## Change the output folder
```bash
python scrape.py --outdir test_outputs
```
## Combination of functions
```bash
python scrape.py --categories Travel --max-pages 1 --delay 2 --outdir test_outputs
```




