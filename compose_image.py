"""
compose_image.py

Takes a generated background image and overlays the verse text + reference,
producing a finished 1080x1080 square image ready for Instagram.
"""
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "assets", "fonts")
QUOTE_FONT_PATH = os.path.join(FONT_DIR, "CrimsonPro-Regular.ttf")
REF_FONT_PATH = os.path.join(FONT_DIR, "WorkSans-Regular.ttf")

CANVAS_SIZE = 1080


def _fit_font_size(draw, text, font_path, max_width, max_height, start_size=80, min_size=32):
    """Shrinks font size until the wrapped text fits within max_width/max_height."""
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        avg_char_w = font.getlength("n")
        wrap_width = max(10, int(max_width / max_char_w(font)))
        wrapped = textwrap.fill(text, width=wrap_width)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=size * 0.35)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_width and h <= max_height:
            return font, wrapped
        size -= 4
    font = ImageFont.truetype(font_path, min_size)
    wrap_width = max(10, int(max_width / max_char_w(font)))
    wrapped = textwrap.fill(text, width=wrap_width)
    return font, wrapped


def max_char_w(font):
    # Rough average character width for wrap-width estimation.
    sample = "abcdefghijklmnopqrstuvwxyz"
    return font.getlength(sample) / len(sample) * 1.9


def compose(background_path: str, verse_text: str, reference: str, out_path: str):
    img = Image.open(background_path).convert("RGB")
    img = img.resize((CANVAS_SIZE, CANVAS_SIZE))

    # Darken the lower two-thirds so white text stays readable regardless
    # of the AI-generated background.
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    grad = ImageDraw.Draw(overlay)
    for y in range(CANVAS_SIZE):
        # Stronger darkening toward the bottom.
        alpha = int(180 * max(0, (y - CANVAS_SIZE * 0.25) / (CANVAS_SIZE * 0.75)))
        grad.line([(0, y), (CANVAS_SIZE, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)

    draw = ImageDraw.Draw(img)

    padding = 90
    max_width = CANVAS_SIZE - padding * 2
    max_height = int(CANVAS_SIZE * 0.5)

    quote_text = f"\u201c{verse_text}\u201d"
    font, wrapped = _fit_font_size(draw, quote_text, QUOTE_FONT_PATH, max_width, max_height)

    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=font.size * 0.35)
    text_h = bbox[3] - bbox[1]
    text_y = CANVAS_SIZE - padding - text_h - 70  # leave room for reference below

    draw.multiline_text(
        (CANVAS_SIZE / 2, text_y),
        wrapped,
        font=font,
        fill=(255, 255, 255, 255),
        anchor="ma",
        align="center",
        spacing=font.size * 0.35,
    )

    ref_font = ImageFont.truetype(REF_FONT_PATH, 34)
    ref_y = CANVAS_SIZE - padding
    draw.text(
        (CANVAS_SIZE / 2, ref_y),
        reference.upper(),
        font=ref_font,
        fill=(230, 220, 200, 255),
        anchor="ma",
        align="center",
    )

    final = img.convert("RGB")
    final.save(out_path, quality=95)
    return out_path
