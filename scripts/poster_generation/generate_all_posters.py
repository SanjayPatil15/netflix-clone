import os
import re
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# === SETTINGS ===
MOVIES_CSV_PATH = "data/movielens/movies.csv"  # Path to your movies.csv
POSTERS_DIR = "static/posters"
FONT_PATH = None  # Optional: use a .ttf cinematic font
DEFAULT_COLOR_TOP = (200, 0, 0)  # Netflix Red
DEFAULT_COLOR_BOTTOM = (10, 0, 0)  # Dark Red / Black

# Create posters directory if missing
os.makedirs(POSTERS_DIR, exist_ok=True)

# Load movies
df = pd.read_csv(MOVIES_CSV_PATH)

def clean_title_for_filename(title: str) -> str:
    """
    Cleans title safely for Windows & Linux file systems.
    Removes illegal characters: \ / * ? : " < > |
    Example: 'M*A*S*H (1970)' ➜ 'MASH_1970.jpg'
    """
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)  # remove illegal characters
    safe_title = safe_title.replace(",", "").replace("'", "")
    safe_title = re.sub(r"[()]", "", safe_title)  # remove parentheses
    safe_title = safe_title.replace(" ", "_")  # replace spaces with _
    return safe_title + ".jpg"

def generate_poster(title: str, save_path: str):
    # Create gradient background (Red → Black)
    width, height = 600, 900
    img = Image.new("RGB", (width, height), DEFAULT_COLOR_BOTTOM)
    draw = ImageDraw.Draw(img)

    # Gradient Fill
    for y in range(height):
        r = int(DEFAULT_COLOR_TOP[0] + (DEFAULT_COLOR_BOTTOM[0] - DEFAULT_COLOR_TOP[0]) * (y / height))
        g = int(DEFAULT_COLOR_TOP[1] + (DEFAULT_COLOR_BOTTOM[1] - DEFAULT_COLOR_TOP[1]) * (y / height))
        b = int(DEFAULT_COLOR_TOP[2] + (DEFAULT_COLOR_BOTTOM[2] - DEFAULT_COLOR_TOP[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Load or fallback font
    try:
        font = ImageFont.truetype(FONT_PATH or "arialbd.ttf", 70)  # Bold Netflix-style
    except:
        font = ImageFont.load_default()

    # Split title to fit layout
    max_width = width - 60
    words = title.split()
    line = ""
    lines = []

    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Draw centered text
    y_offset = height // 2 - len(lines) * 40
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2]
        x = (width - text_w) // 2

        # Glow outline for cinematic effect
        for glow in range(2):
            draw.text((x+2, y_offset+2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y_offset), line, font=font, fill=(255, 255, 255))

        y_offset += 80

    img.save(save_path)
    print(f"✅ Poster created → {save_path}")

print("🎬 Generating CLEAN RED Netflix-style posters for ALL movies...")

for idx, row in df.iterrows():
    title = row["title"]
    filename = clean_title_for_filename(title)
    save_path = os.path.join(POSTERS_DIR, filename)

    # Only generate if not already present
    if not os.path.exists(save_path):
        generate_poster(title, save_path)

print("\n🔥 DONE! Posters ready in static/posters/. Now run: python app.py")
