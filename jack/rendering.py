"""Render the original top-ten map cards without shared temporary files."""

import random
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).parent / "assets"
MAPS = ("dream_grove.png", "lectus.png", "jurassic.png")


def render_leaderboard(title: str, rows: list[tuple[str, float]]) -> BytesIO:
    with Image.open(ASSETS / random.choice(MAPS)) as background:
        image = background.convert("RGB").resize((1000, 1000))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(ASSETS / "minecraft.otf"), 32)
    heading = ImageFont.truetype(str(ASSETS / "minecraft.otf"), 38)
    draw.text(
        (45, 80),
        "Jack | " + title,
        font=heading,
        fill="#249d9f",
        stroke_width=2,
        stroke_fill="black",
    )
    if not rows:
        draw.text((45, 230), "No players yet.", font=font, fill="white")
    for index, (name, value) in enumerate(rows[:10], start=1):
        y = 170 + index * 65
        draw.text(
            (45, y),
            f"{index}. {name[:16]}",
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill="black",
        )
        label = f"{value:,.2f}".rstrip("0").rstrip(".")
        width = draw.textlength(label, font=font)
        draw.text(
            (955 - width, y), label, font=font, fill="#ffd700", stroke_width=2, stroke_fill="black"
        )
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output
