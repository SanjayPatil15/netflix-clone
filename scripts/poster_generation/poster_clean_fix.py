import os
from PIL import Image, ImageStat

POSTER_DIR = "static/posters"
BRIGHTNESS_THRESHOLD = 40  # Too dark = corrupted placeholder

def is_dark_image(img_path):
    try:
        img = Image.open(img_path).convert("L")  # Convert to grayscale
        stat = ImageStat.Stat(img)
        brightness = stat.mean[0]  # Average pixel brightness

        # If extremely dark or completely black -> treat as invalid
        return brightness < BRIGHTNESS_THRESHOLD
    except:
        return True  # If unreadable -> delete

def clean_dark_posters():
    removed = 0
    for file in os.listdir(POSTER_DIR):
        if file.lower().endswith(".jpg"):
            path = os.path.join(POSTER_DIR, file)
            if is_dark_image(path):
                print(f"❌ Removing dark/broken poster → {file}")
                os.remove(path)
                removed += 1
    print(f"\n✅ Cleanup Complete — Removed {removed} bad posters.")

if __name__ == "__main__":
    if not os.path.exists(POSTER_DIR):
        print("⚠️ posters folder not found!")
    else:
        print("🎯 Scanning and cleaning corrupted posters...\n")
        clean_dark_posters()
