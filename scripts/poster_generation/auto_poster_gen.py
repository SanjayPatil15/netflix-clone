# 🎬 AUTO POSTER GENERATOR — Top 50 Movies from movies.csv with Netflix-Style Gradient
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from utils.DataLoader import DataLoader

# ✅ Paths
STATIC_POSTER_DIR = "static/posters"
FONT_PATH = "C:/Windows/Fonts/arialbd.ttf"  # ✅ Change only if this path doesn't exist on your system

# ✅ Ensure folder exists
os.makedirs(STATIC_POSTER_DIR, exist_ok=True)

# ✅ Load your existing dataset (NOT asking you to download anything new)
loader = DataLoader("data/movielens", "data/wikipedia")
movies_df = loader.load_movies_data()

# ✅ Take Top 50 Movies (if less, take all)
top_movies = movies_df.head(50)["title"].tolist()

# ✅ Colors for gradient theme
GRADIENT_START = (229, 9, 20)   # Netflix Red
GRADIENT_END = (0, 0, 0)        # Fade to Black

def generate_gradient_poster(title, save_path):
    width, height = 600, 900
    img = Image.new("RGB", (width, height), color=GRADIENT_START)
    draw = ImageDraw.Draw(img)

    # 🎨 Create vertical gradient
    for y in range(height):
        r = int(GRADIENT_START[0] + (GRADIENT_END[0] - GRADIENT_START[0]) * (y / height))
        g = int(GRADIENT_START[1] + (GRADIENT_END[1] - GRADIENT_START[1]) * (y / height))
        b = int(GRADIENT_START[2] + (GRADIENT_END[2] - GRADIENT_START[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ✍ Add Movie Title
    try:
        font = ImageFont.truetype(FONT_PATH, 48)
    except:
        font = ImageFont.load_default()

    text = title.upper()

    # ✅ FIXED: Compatible with latest Pillow
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw.text(
        ((width - text_w) // 2, height // 2 - text_h // 2),
        text,
        font=font,
        fill=(255, 255, 255)
    )

    # ✅ Save the image
    img.save(save_path, "JPEG")
    print(f"✅ Poster created: {save_path}")


# 🚀 Generate posters
print("🎬 Generating Netflix-style posters for Top 50 movies...")
for title in top_movies:
    clean_name = title.replace(" ", "_").replace("/", "_")
    save_path = os.path.join(STATIC_POSTER_DIR, f"{clean_name}.jpg")
    generate_gradient_poster(title, save_path)

print("\n🎉 DONE! Check static/posters/ for auto-generated posters!")
print("🔥 Now reload your web app — posters will start showing automatically.")
