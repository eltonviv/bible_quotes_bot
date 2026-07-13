"""
main.py

Runs one full daily cycle:
  1. Load (or download) the full KJV text.
  2. Pick the next quote-worthy verse based on saved progress.
  3. Generate AI artwork matching the verse's mood.
  4. Overlay the verse text onto the artwork.
  5. Save the finished 1080x1080 image to output/ and update state.json.

This script only PRODUCES the image -- posting to Instagram is a separate
step (see post_to_instagram.py, added once the content pipeline is solid).
"""
import datetime
import json
import os

from bible_data import load_full_bible
from curated_selector import load_state, save_state, load_curated_list, pick_next_curated_verse
from image_gen import generate_image
from compose_image import compose

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
OUTPUT_DIR = os.path.join(HERE, "output")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    full_bible = load_full_bible()
    curated_list = load_curated_list()
    state = load_state()

    new_state, reference, verse_text = pick_next_curated_verse(full_bible, curated_list, state)

    today = datetime.date.today().isoformat()
    raw_path = os.path.join(OUTPUT_DIR, f"{today}_raw.jpg")
    final_path = os.path.join(OUTPUT_DIR, f"{today}_post.jpg")

    print(f"Selected verse: {reference} -> {verse_text}")
    print("Generating AI artwork...")
    generate_image(verse_text, raw_path, seed=hash(reference) % 100000)

    print("Composing final post image...")
    compose(raw_path, verse_text, reference, final_path)

    # Save metadata alongside the image. "image_relpath" is the path relative
    # to the repo root, used by the workflow to build the public raw.githubusercontent.com URL.
    meta_path = os.path.join(OUTPUT_DIR, f"{today}_meta.json")
    image_relpath = os.path.relpath(final_path, HERE)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {"reference": reference, "text": verse_text, "image_relpath": image_relpath},
            f, indent=2,
        )

    save_state(new_state)
    print(f"Done. Saved {final_path}")
    print(f"Next run will continue from curated_index={new_state['curated_index']}")


if __name__ == "__main__":
    main()
