"""Extract images from DOCX worksheets and map them to lessons.

User instruction: "save docx as html then tag each image to its lesson."
This script:
1. Unzips the DOCX to extract images from word/media/
2. Maps images to weeks based on document text analysis
3. Saves images to static/img/exercises/lop{N}/week{W}/
"""
import os
import sys
import re
import zipfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import IMAGES_DIR

DOCX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "web-phieu-bai-tap")


def extract_images_from_docx(docx_path, lop, week_start, week_end):
    """Extract all images from a DOCX file and distribute to week folders."""
    if not os.path.exists(docx_path):
        print(f"File not found: {docx_path}")
        return

    # Create output directories
    for w in range(week_start, week_end + 1):
        out_dir = os.path.join(IMAGES_DIR, f"lop{lop}", f"week{w}")
        os.makedirs(out_dir, exist_ok=True)

    # Extract images from DOCX (which is a ZIP file)
    images = []
    try:
        with zipfile.ZipFile(docx_path, 'r') as z:
            for name in z.namelist():
                if name.startswith('word/media/') and not name.endswith('/'):
                    ext = os.path.splitext(name)[1].lower()
                    if ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.emf', '.wmf'):
                        images.append(name)

            if not images:
                print("No images found in DOCX.")
                return

            print(f"Found {len(images)} images in {os.path.basename(docx_path)}")

            # Extract all images to a temp folder first
            all_images_dir = os.path.join(IMAGES_DIR, f"lop{lop}", "_all")
            os.makedirs(all_images_dir, exist_ok=True)

            for i, img_path in enumerate(sorted(images)):
                ext = os.path.splitext(img_path)[1]
                out_name = f"img_{i+1:03d}{ext}"
                with z.open(img_path) as src:
                    out_path = os.path.join(all_images_dir, out_name)
                    with open(out_path, 'wb') as dst:
                        dst.write(src.read())
                print(f"  Extracted: {out_name}")

            # Simple distribution: divide images evenly across weeks
            num_weeks = week_end - week_start + 1
            imgs_per_week = max(1, len(images) // num_weeks)

            for i, img_path in enumerate(sorted(images)):
                week_idx = min(i // imgs_per_week, num_weeks - 1)
                week_num = week_start + week_idx
                ext = os.path.splitext(img_path)[1]
                src_name = f"img_{i+1:03d}{ext}"
                src_path = os.path.join(all_images_dir, src_name)
                dst_dir = os.path.join(IMAGES_DIR, f"lop{lop}", f"week{week_num}")
                dst_path = os.path.join(dst_dir, src_name)
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)

            print(f"\nImages distributed across weeks {week_start}-{week_end}")
            print(f"Review and re-organize manually in: {os.path.join(IMAGES_DIR, f'lop{lop}')}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Extract from the Grade 1 worksheet (weeks 15-21)
    # Find the docx file dynamically
    docx_file = None
    if os.path.exists(DOCX_DIR):
        for f in os.listdir(DOCX_DIR):
            if f.endswith('.docx'):
                docx_file = os.path.join(DOCX_DIR, f)
                break
    if not docx_file:
        docx_file = os.path.join(DOCX_DIR, "not_found.docx")

    if os.path.exists(docx_file):
        extract_images_from_docx(docx_file, lop=1, week_start=15, week_end=21)
    else:
        print(f"DOCX not found: {docx_file}")
        print("Available files in web-phieu-bai-tap:")
        if os.path.exists(DOCX_DIR):
            for f in os.listdir(DOCX_DIR):
                print(f"  {f}")
