# ✅ FULLY FIXED POSTER GENERATOR — SAFE FOR WINDOWS

import os
import re
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

POSTERS_DIR = "static/posters"
DEFAULT_FONT = "arial.ttf"  # If not found, fallback will be used

os.makedirs(POSTERS_DIR, exist_ok=True)

# ✅ Load movies
movies = pd.read_csv("data/movielens/movies.csv") if os.path.exists("data/movielens/movies.csv") else None
if movies is None:
    print("❌ movies.csv not found! Exiting.")
    exit()

def clean_filename(title: str) -> str:
    """
    Clean title for safe Windows filename:
    Removes * : ? " < > | \ / and replaces spaces.
    """
    title = re.sub(r"[<>:\"/\\|?*]", "", title)  # Remove illegal characters
    title = title.replace(" ", "_")  # Replace spaces with underscores
    title = title.replace(",", "")   # Remove commas
    return title + ".jpg"

def generate_poster(text, save_path):
    """
    Generates a basic gradient-style poster with the movie title.
    """
    img = Image.new("RGB", (300, 450), "#111")
    draw = ImageDraw.Draw(img)

    # Gradient effect
    for i in range(450):
        r = int(229 - (i / 450) * 100)
        draw.line([(0, i), (300, i)], fill=(r, 9, 20))

    # Load font
    try:
        font = ImageFont.truetype(DEFAULT_FONT, 20)
    except:
        font = ImageFont.load_default()

    # Centered text
    y_offset = 180
    for line in text.split(" "):
        w, h = draw.textbbox((0, 0), line, font=font)[2:]  # fixed for PIL 10+
        x = (300 - w) // 2
        draw.text((x, y_offset), line, font=font, fill="white")
        y_offset += h + 5

    img.save(save_path)

print(f"🎬 Checking {len(movies)} movies for missing posters...")

missing_count = 0
for _, row in movies.iterrows():
    title = str(row["title"])
    filename = clean_filename(title)
    poster_path = os.path.join(POSTERS_DIR, filename)

    if not os.path.exists(poster_path):
        generate_poster(title[:25], poster_path)
        print(f"✅ Poster created: {filename}")
        missing_count += 1

print(f"\n🎉 DONE! {missing_count} posters generated!")
print("🔥 Now reload your web app to see updated posters.")
