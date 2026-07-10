"""
image_gen.py

Turns a verse's text into an AI-artwork prompt and generates a square image
via Pollinations.ai -- a free, keyless image generation API. Good enough for
a daily automation; swap in Stability AI / OpenAI Images later if you want
higher, more consistent quality (both have small per-image costs).
"""
import os
import urllib.parse
import urllib.request

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1080&nologo=true&seed={seed}"

# Simple keyword -> visual mood mapping. Falls back to a generic serene style.
MOOD_MAP = [
    (["light", "shine", "glory", "sun"], "radiant golden light breaking through clouds, ethereal"),
    (["water", "sea", "flood", "river", "waters"], "vast calm ocean at dawn, gentle waves, misty horizon"),
    (["garden", "tree", "fruit", "earth", "ground"], "lush ancient garden landscape, soft morning mist"),
    (["fear not", "strength", "courage", "strong"], "dramatic mountain peak at sunrise, vast sky, sense of scale"),
    (["love", "heart", "comfort", "mercy", "kind"], "warm soft sunset glow, gentle clouds, tranquil"),
    (["night", "star", "stars", "heaven", "sky"], "starry night sky over quiet hills, deep blues"),
    (["shepherd", "sheep", "flock"], "pastoral hillside at golden hour, distant flock, soft light"),
    (["desert", "wilderness"], "vast desert dunes under a glowing sky, solitary and quiet"),
    (["fire", "flame", "burning"], "warm glowing flame light, dramatic shadows, reverent mood"),
]

DEFAULT_MOOD = "serene atmospheric landscape, soft golden light, minimal and reverent"


def build_prompt(verse_text: str) -> str:
    t = verse_text.lower()
    mood = DEFAULT_MOOD
    for keywords, description in MOOD_MAP:
        if any(kw in t for kw in keywords):
            mood = description
            break
    return (
        f"{mood}, fine art digital painting, cinematic lighting, "
        f"no text, no words, no letters, no people faces, high detail, square composition"
    )


def generate_image(verse_text: str, out_path: str, seed: int = 0) -> str:
    """Generates an image for the given verse text and saves it to out_path."""
    prompt = build_prompt(verse_text)
    encoded_prompt = urllib.parse.quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded_prompt, seed=seed)

    req = urllib.request.Request(url, headers={"User-Agent": "daily-verse-bot/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    with open(out_path, "wb") as f:
        f.write(data)

    return out_path
