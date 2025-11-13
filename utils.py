import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin
import requests

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"

def absolute_url(base: str, rel: str) -> str:
    return urljoin(base, rel)

def download_file(session, url: str, path: Path, chunk_size=8192):
    resp = session.get(url, stream=True, timeout=20)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size):
            f.write(chunk)
