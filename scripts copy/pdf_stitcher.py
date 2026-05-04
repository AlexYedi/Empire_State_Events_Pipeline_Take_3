import os
import re
import time
from pypdf import PdfWriter

# --- CONFIG ---
SOURCE_DIR = os.path.expanduser("~/Desktop/Stitches")

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def stitch_pdfs():
    print(f"🔍 Scanning: {SOURCE_DIR}")
    
    if not os.path.exists(SOURCE_DIR):
        print("❌ ERROR: Folder 'Stitches' not found.")
        return

    merger = PdfWriter()
    
    # 1. ONLY pull files that start with 'part_' to avoid duplicates/masters
    # 2. Convert to a 'set' then back to 'list' to guarantee no duplicates
    raw_files = [f for f in os.listdir(SOURCE_DIR) 
                 if f.lower().startswith('part_') and f.lower().endswith('.pdf')]
    
    files = list(set(raw_files)) 
    files.sort(key=natural_sort_key)
    
    if not files:
        print("❌ No files starting with 'part_' found.")
        return

    print(f"📝 Stitching {len(files)} parts in linear order:")
    
    for file in files:
        path = os.path.join(SOURCE_DIR, file)
        print(f"  🔗 Appending: {file}")
        merger.append(path)

    # Output filename - named differently to avoid being picked up next time
    output_name = f"FINAL_MASTER_{time.strftime('%H%M%S')}.pdf"
    output_path = os.path.join(SOURCE_DIR, output_name)

    try:
        with open(output_path, "wb") as f:
            merger.write(f)
        merger.close()
        print(f"\n✅ SUCCESS: Linear merge complete.")
        print(f"📄 Created: {output_name}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    stitch_pdfs()