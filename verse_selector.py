"""
verse_selector.py

Walks through the Bible in canonical order, one chapter at a time, starting
at Genesis 1. For each chapter it scores every verse for "quotability" and
picks the best one. If a chapter has nothing quote-worthy (e.g. a genealogy
list), it moves on to the next chapter automatically until it finds a verse
that clears the bar -- so every day still produces exactly one quote.

Progress is stored in state.json so re-running the script continues from
where it left off instead of repeating verses.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "state.json")

# Words/phrases that tend to signal an uplifting, quotable line.
POSITIVE_KEYWORDS = [
    "love", "hope", "faith", "light", "life", "peace", "grace", "glory",
    "mercy", "wisdom", "truth", "joy", "strength", "trust", "comfort",
    "courage", "blessed", "blessing", "good", "righteous", "salvation",
    "heart", "soul", "eternal", "shepherd", "guide", "healed", "heal",
    "forgive", "forgiveness", "kindness", "patience", "gentle", "still",
    "rest", "renew", "redeem", "shine", "fear not", "be strong",
]

# Patterns that signal genealogy / census / list verses -- almost never quotable.
GENEALOGY_PATTERNS = [
    r"\bbegat\b",
    r"\bthe son of\b.*\bthe son of\b",  # repeated "son of" chains
    r"^and \w+ (lived|died)\b",
    r"lived.{0,20}(hundred|thousand).{0,20}years",
    r"son of.{0,40}son of",
    r"\bin the \w+ year\b",              # "in the tenth year", regnal-year markers
    r"numbered.{0,20}(thousand|hundred)", # census counts
    r"these are the generations",
]


def _word_count(text):
    return len(text.split())


def score_verse(text):
    """Return a quotability score for a single verse. Higher is better."""
    t = text.lower()

    # Hard disqualifiers: genealogy / list verses, and fragments too short
    # to stand alone as a quote (e.g. "And it was so.").
    if len(text) <= 30:
        return -1
    for pat in GENEALOGY_PATTERNS:
        if re.search(pat, t):
            return -1

    words = _word_count(text)
    # Ideal length for a social post: not a fragment, not a wall of text.
    if words < 6 or words > 32:
        length_score = 0
    elif 8 <= words <= 22:
        length_score = 3
    else:
        length_score = 1.5

    keyword_score = sum(1 for kw in POSITIVE_KEYWORDS if kw in t)

    # Slight penalty for verses that are mostly proper nouns / commas (lists).
    comma_count = text.count(",")
    list_penalty = 1 if comma_count >= 4 else 0

    return length_score + keyword_score - list_penalty


def best_verse_in_chapter(chapter_verses, min_score=2):
    """chapter_verses: dict[int verse_num -> text]. Returns (verse_num, text, score) or None."""
    best = None
    for vnum in sorted(chapter_verses.keys()):
        text = chapter_verses[vnum]
        s = score_verse(text)
        if best is None or s > best[2]:
            best = (vnum, text, s)
    if best and best[2] >= min_score:
        return best
    return None


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Start at the very beginning: Genesis, chapter 1.
    return {"book_index": 0, "chapter": 1}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def pick_next_verse(full_bible, book_order, state, min_score=4, max_chapters_to_scan=50,
                     use_llm=False):
    """
    Advances through book_order/chapters starting at state's position until
    it finds a quote-worthy verse. Mutates and returns the updated state
    plus the chosen reference and text.

    use_llm=True routes selection through llm_selector (Claude judges each
    chapter for real quotability). Falls back to the keyword heuristic if
    that raises (e.g. no API key set).
    """
    scanned = 0
    book_index = state["book_index"]
    chapter = state["chapter"]

    while scanned < max_chapters_to_scan:
        if book_index >= len(book_order):
            # Reached the end of the Bible -- loop back to Genesis 1.
            book_index = 0
            chapter = 1

        book_name = book_order[book_index]["name"]
        book_chapters = full_bible.get(book_name, {})
        chapter_verses = book_chapters.get(str(chapter)) or book_chapters.get(chapter)

        if chapter_verses is None:
            # No more chapters in this book -- move to the next book.
            book_index += 1
            chapter = 1
            scanned += 1
            continue

        # Normalize keys to int for consistent lookups downstream.
        chapter_verses = {int(k): v for k, v in chapter_verses.items()}

        result = None
        if use_llm:
            try:
                from llm_selector import select_best_verse_llm
                llm_result = select_best_verse_llm(chapter_verses, book_name, chapter)
                if llm_result is not None:
                    vnum, text = llm_result
                    result = (vnum, text, None)
            except Exception as e:
                print(f"[warn] LLM selection failed ({e}), falling back to heuristic.")
                result = best_verse_in_chapter(chapter_verses, min_score=min_score)
        else:
            result = best_verse_in_chapter(chapter_verses, min_score=min_score)

        # Always advance the pointer past this chapter for next time.
        next_chapter = chapter + 1
        next_book_index = book_index

        if result is not None:
            vnum, text, score = result
            new_state = {"book_index": next_book_index, "chapter": next_chapter}
            reference = f"{book_name} {chapter}:{vnum}"
            return new_state, reference, text.strip()

        # Nothing quotable in this chapter -- keep scanning forward.
        book_index = next_book_index
        chapter = next_chapter
        scanned += 1

    raise RuntimeError("Scanned too many chapters without finding a quotable verse.")
