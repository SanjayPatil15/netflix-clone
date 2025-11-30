# 🎨 AUTO GENERATE NETFLIX-STYLE GENRE POSTERS
from PIL import Image, ImageDraw, ImageFont, ImageColor
import os

# 🎭 Genre Gradient Themes
GENRE_STYLES = {
    "action": ("#FF0000", "#8B0000"),
    "romance": ("#FF1493", "#C71585"),
    "comedy": ("#FFD700", "#FF8C00"),
    "thriller": ("#4A148C", "#000000"),
    "sci-fi": ("#00BFFF", "#00008B"),
    "ai": ("#00FFCC", "#006666")
}

# ✅ Ensure output folder exists
OUTPUT_DIR = "static/genre_posters"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ✅ Try loading a good font — fallback safe
try:
    FONT = ImageFont.truetype("arial.ttf", 100)
except:
    FONT = ImageFont.load_default()

def generate_genre_poster(text, filename, colors):
    """Generate a smooth gradient cinematic-style poster"""
    img = Image.new("RGB", (800, 450), color=colors[0])
    draw = ImageDraw.Draw(img)

    # 🎨 Gradient Blend
    for y in range(450):
        r1, g1, b1 = ImageColor.getrgb(colors[0])
        r2, g2, b2 = ImageColor.getrgb(colors[1])
        r = int(r1 + (r2 - r1) * (y / 450))
        g = int(g1 + (g2 - g1) * (y / 450))
        b = int(b1 + (b2 - b1) * (y / 450))
        draw.line([(0, y), (800, y)], fill=(r, g, b))

    # ✨ Add Title Text
    w, h = draw.textbbox((0, 0), text, font=FONT)[2:]
    x = (800 - w) // 2
    y = (450 - h) // 2
    draw.text((x, y), text, font=FONT, fill="white")

    img.save(os.path.join(OUTPUT_DIR, filename))
    print(f"✅ Created: {filename}")

if __name__ == "__main__":
    print("🎬 Generating GENRE POSTERS...")
    for genre_name, colors in GENRE_STYLES.items():
        filename = f"{genre_name}.jpg"
        generate_genre_poster(genre_name.upper(), filename, colors)
    print("🔥 Posters Ready! Check static/genre_posters/")
