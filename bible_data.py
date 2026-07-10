"""
bible_data.py

Downloads the full King James Version (public domain) text once and caches
it locally as data/kjv_full.json, so daily runs don't need network access
for the text itself. Source: aruljohn/Bible-kjv on GitHub (public domain KJV).
"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
BOOKS_FILE = os.path.join(DATA_DIR, "books.json")
CACHE_FILE = os.path.join(DATA_DIR, "kjv_full.json")

BASE_URL = "https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/{}.json"


def load_book_list():
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def download_full_bible():
    """Fetch every book from the source repo and save one combined JSON file.
    Only needs to run once (or whenever the cache is missing)."""
    books = load_book_list()
    full = {}
    for b in books:
        url = BASE_URL.format(b["file"])
        print(f"Downloading {b['name']}...")
        with urllib.request.urlopen(url) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        chapters = {}
        for ch in raw["chapters"]:
            chapter_num = int(ch["chapter"])
            verses = {int(v["verse"]): v["text"] for v in ch["verses"]}
            chapters[chapter_num] = verses
        full[b["name"]] = chapters

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False, indent=1)
    print(f"Saved full KJV text to {CACHE_FILE}")
    return full


def load_full_bible():
    """Load the cached Bible text, downloading it first if needed."""
    if not os.path.exists(CACHE_FILE):
        return download_full_bible()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    download_full_bible()
