import os
import re
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

# === SETTINGS ===
MOVIES_CSV_PATH = "data/movielens/movies.csv"
POSTERS_DIR = "static/posters"
DEFAULT_COLOR_TOP = (200, 0, 0)  # Netflix Red
DEFAULT_COLOR_BOTTOM = (10, 0, 0)  # Dark Black Red

# ✅ Make sure directory exists and is CLEAN
if os.path.exists(POSTERS_DIR):
    for f in os.listdir(POSTERS_DIR):
        if f.endswith(".jpg"):
            os.remove(os.path.join(POSTERS_DIR, f))
else:
    os.makedirs(POSTERS_DIR, exist_ok=True)

# ✅ Load movie titles
df = pd.read_csv(MOVIES_CSV_PATH)

def clean_filename(title: str) -> str:
    t = re.sub(r"[^\w\s]", "", title)  # Remove symbols
    t = t.replace(" ", "_")
    m = re.search(r"(\d{4})", title)
    year = m.group(1) if m else ""
    return f"{t}_{year}.jpg"

def generate_red_poster(title: str, save_path: str):
    width, height = 600, 900
    img = Image.new("RGB", (width, height), DEFAULT_COLOR_BOTTOM)
    draw = ImageDraw.Draw(img)

    # ✅ Smooth vertical gradient
    for y in range(height):
        r = int(DEFAULT_COLOR_TOP[0] + (DEFAULT_COLOR_BOTTOM[0] - DEFAULT_COLOR_TOP[0]) * (y / height))
        g = int(DEFAULT_COLOR_TOP[1] + (DEFAULT_COLOR_BOTTOM[1] - DEFAULT_COLOR_TOP[1]) * (y / height))
        b = int(DEFAULT_COLOR_TOP[2] + (DEFAULT_COLOR_BOTTOM[2] - DEFAULT_COLOR_TOP[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ✅ Use built-in font (automatic fallback)
    try:
        font = ImageFont.truetype("arialbd.ttf", 70)
    except:
        font = ImageFont.load_default()

    # ✅ Center Text
    text = title[:22]  # Limit long titles
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # ✅ Light glow effect
    draw.text((x+3, y+3), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    img.save(save_path)
    print(f"✅ Created → {save_path}")

print("🎬 Generating FINAL RED posters for ALL movies...")
for idx, row in df.iterrows():
    title = row["title"]
    filename = clean_filename(title)
    save_path = os.path.join(POSTERS_DIR, filename)
    generate_red_poster(title, save_path)

print("\n🔥 ALL DONE! Posters ready. Launch app now with: python app.py")
