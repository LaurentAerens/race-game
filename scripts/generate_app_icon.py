"""
Generates high-resolution app icon assets for Open-Wheel Motorsport Management Tycoon.
Produces:
    - data/app_icon.png (512x512 RGBA with transparent squircle corners)
    - data/app_icon.ico (Windows multi-resolution icon with 16, 24, 32, 48, 64, 128, 256 px)
"""

import os
import sys

from PIL import Image, ImageDraw


def generate_icons(source_image_path: str, output_dir: str) -> None:
    if not os.path.exists(source_image_path):
        raise FileNotFoundError(f"Source image not found: {source_image_path}")

    os.makedirs(output_dir, exist_ok=True)
    img = Image.open(source_image_path).convert("RGBA")
    w, h = img.size

    # Create high-res supersampled mask for rounded squircle corners
    scale = 4
    mask = Image.new("L", (w * scale, h * scale), 0)
    draw = ImageDraw.Draw(mask)

    # Outer margin and corner radius scaled
    margin = 12 * scale
    radius = 185 * scale
    draw.rounded_rectangle([margin, margin, (w * scale) - margin, (h * scale) - margin], radius=radius, fill=255)
    mask = mask.resize((w, h), Image.Resampling.LANCZOS)

    # Apply mask to alpha channel
    img.putalpha(mask)

    # 1. Save 512x512 PNG
    icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    png_path = os.path.join(output_dir, "app_icon.png")
    icon_512.save(png_path, format="PNG", optimize=True)
    print(f"[OK] Saved {png_path}")

    # 2. Save multi-resolution Windows ICO
    ico_path = os.path.join(output_dir, "app_icon.ico")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_512.save(ico_path, format="ICO", sizes=sizes)
    print(f"[OK] Saved {ico_path}")


if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_source = os.path.join(project_root, "data", "app_icon.png")
    default_out = os.path.join(project_root, "data")
    source = sys.argv[1] if len(sys.argv) > 1 else default_source
    generate_icons(source, default_out)
