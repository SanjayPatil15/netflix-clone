from PIL import Image, UnidentifiedImageError
import os

folder = "static/genres"  # 👈 change target folder
print(f"📂 Checking files in: {folder}\n")

converted = 0
failed = []

for file in os.listdir(folder):
    file_path = os.path.join(folder, file)
    name, ext = os.path.splitext(file)
    ext_lower = ext.lower()

    if ext_lower == ".jpg":
        continue

    if ext_lower in [".jpeg", ".png", ".webp", ".jfif"]:
        try:
            img = Image.open(file_path)
            rgb_img = img.convert("RGB")
            new_name = f"{name}.jpg"
            new_path = os.path.join(folder, new_name)

            rgb_img.save(new_path, "JPEG", quality=90)
            os.remove(file_path)
            converted += 1
            print(f"✅ Converted: {file} → {new_name}")
        except UnidentifiedImageError:
            print(f"⚠️ Skipped (unrecognized format): {file}")
            failed.append(file)
        except Exception as e:
            print(f"❌ Error converting {file}: {e}")
            failed.append(file)

print("\n🔥 Conversion complete!")
print(f"✅ {converted} files converted to .jpg")

if failed:
    print("\n⚠️ Failed files:")
    for f in failed:
        print(f" - {f}")
