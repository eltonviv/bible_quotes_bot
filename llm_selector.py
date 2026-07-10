"""
llm_selector.py

Uses the Claude API to judge which verse (if any) in a chapter is genuinely
insightful/quotable -- far better judgment than keyword heuristics, since it
understands meaning, not just word matches. Cost is tiny: one short call per
day (a few cents per MONTH at most on Haiku), only used if ANTHROPIC_API_KEY
is set. Falls back to the free heuristic in verse_selector.py otherwise.
"""
import json
import os

MODEL = "claude-haiku-4-5-20251001"


def select_best_verse_llm(chapter_verses: dict, book_name: str, chapter_num: int):
    """
    chapter_verses: dict[int -> str]
    Returns (verse_num, text) for the best verse, or None if nothing in this
    chapter is genuinely quotable (e.g. a pure genealogy list) -- signalling
    the caller to move on to the next chapter.
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "The 'anthropic' package isn't installed. Run: pip install anthropic"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")

    client = anthropic.Anthropic(api_key=api_key)

    numbered = "\n".join(f"{v}: {t}" for v, t in sorted(chapter_verses.items()))

    prompt = f"""You are choosing ONE verse from {book_name} chapter {chapter_num} (KJV) to feature \
as a daily inspirational quote on a social media account. The verse must stand \
alone as meaningful, insightful, or inspiring without extra context -- not a \
genealogy line, not a narrative detail like "so-and-so begat so-and-so", and \
not a fragment that only makes sense mid-story.

Verses:
{numbered}

If a genuinely quotable verse exists, respond with ONLY this JSON, nothing else:
{{"verse": <verse_number>}}

If NONE of the verses in this chapter stand alone as inspirational (e.g. it's \
entirely genealogy or narrative logistics), respond with ONLY:
{{"verse": null}}"""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.content[0].text.strip()
    # Be tolerant of stray markdown fences.
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    vnum = parsed.get("verse")
    if vnum is None:
        return None
    vnum = int(vnum)
    if vnum not in chapter_verses:
        return None
    return vnum, chapter_verses[vnum].strip()
