"""
curated_selector.py

Option A: cycles through a hand-picked list of well-known, standalone
inspirational KJV verses (data/curated_verses.json) instead of scanning the
Bible sequentially. No API key, no billing, no risk of a weak pick slipping
through -- every verse in the list was chosen because it already reads well
on its own.

Trade-off: the list currently has ~190 verses, so it repeats every ~190
days (roughly twice a year at one post/day). Easy to extend later --
just add more "Book Chapter:Verse" strings to data/curated_verses.json.

Progress is stored in state.json (key "curated_index") so re-running
continues from where it left off.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
CURATED_FILE = os.path.join(DATA_DIR, "curated_verses.json")
STATE_FILE = os.path.join(HERE, "state.json")

REF_PATTERN = re.compile(r"^(.+?)\s+(\d+):(\d+)$")


def load_curated_list():
    with open(CURATED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        if "curated_index" in state:
            return state
    return {"curated_index": 0}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_verse_text(full_bible, reference):
    """reference like 'Psalms 23:1' -> verse text, or None if not found."""
    m = REF_PATTERN.match(reference.strip())
    if not m:
        return None
    book, chapter, verse = m.group(1), m.group(2), m.group(3)

    book_chapters = full_bible.get(book)
    if book_chapters is None:
        return None

    chapter_verses = book_chapters.get(chapter) or book_chapters.get(int(chapter))
    if chapter_verses is None:
        return None

    text = chapter_verses.get(verse) or chapter_verses.get(int(verse))
    return text.strip() if text else None


def pick_next_curated_verse(full_bible, curated_list, state):
    """
    Returns (new_state, reference, text) for the next verse in the curated
    list, wrapping back to the start once the list is exhausted. Skips (and
    warns about) any reference that doesn't resolve against full_bible --
    e.g. a typo -- rather than crashing a scheduled run.
    """
    n = len(curated_list)
    if n == 0:
        raise RuntimeError("Curated verse list is empty.")

    idx = state.get("curated_index", 0) % n

    for attempt in range(n):
        reference = curated_list[idx]
        text = get_verse_text(full_bible, reference)
        next_idx = (idx + 1) % n

        if text:
            new_state = {"curated_index": next_idx}
            return new_state, reference, text

        print(f"[warn] Curated reference '{reference}' not found in Bible text, skipping.")
        idx = next_idx

    raise RuntimeError("No curated references resolved against the Bible text -- check data/curated_verses.json.")
