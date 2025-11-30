import os, re
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

MOVIES_CSV_PATH = "data/movielens/movies.csv"
POSTERS_DIR = "static/posters"
GRAD_START = (200, 0, 0)
GRAD_END = (20, 0, 0)

os.makedirs(POSTERS_DIR, exist_ok=True)
df = pd.read_csv(MOVIES_CSV_PATH)

def clean_filename(title):
    t = re.sub(r"[^\w\s]", "", title)  # Remove brackets and symbols
    t = t.replace(" ", "_")
    m = re.search(r"(\d{4})", title)
    year = m.group(1) if m else ""
    return f"{t}_{year}.jpg"

def generate_poster(title, save_path):
    width, height = 600, 900
    img = Image.new("RGB", (width, height), GRAD_END)
    draw = ImageDraw.Draw(img)

    # Red gradient shading
    for y in range(height):
        r = GRAD_START[0] + (GRAD_END[0] - GRAD_START[0]) * (y / height)
        g = GRAD_START[1] + (GRAD_END[1] - GRAD_START[1]) * (y / height)
        b = GRAD_START[2] + (GRAD_END[2] - GRAD_START[2]) * (y / height)
        draw.line([(0, y), (width, y)], fill=(int(r), int(g), int(b)))

    try:
        font = ImageFont.truetype("arialbd.ttf", 72)
    except:
        font = ImageFont.load_default()

    # Center title
    text = title.split("(")[0][:20]  # shorten long names
    w, h = draw.textbbox((0, 0), text, font=font)[2:]
    x = (width - w) // 2
    y = height // 2 - 40

    draw.text((x-2, y-2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    img.save(save_path)
    print(f"✅ Poster generated → {save_path}")

print("🎨 Regenerating missing posters...\n")
for _, row in df.iterrows():
    title = row["title"]
    filename = clean_filename(title)
    save_path = os.path.join(POSTERS_DIR, filename)
    if not os.path.exists(save_path):
        generate_poster(title, save_path)

print("\n🚀 Done! Refresh your app and confirm all posters show as RED.")
