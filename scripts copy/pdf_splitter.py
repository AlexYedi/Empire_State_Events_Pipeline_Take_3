import os
import re
import glob
from pypdf import PdfReader, PdfWriter

# --- DYNAMIC CONFIG ---
# Points to your stitches folder
BASE_DIR = os.path.expanduser("~/Documents/scripts/stitches")
OUTPUT_DIR = os.path.join(BASE_DIR, "chapters")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_latest_pdf():
    """Finds the most recently created PDF in the folder, ignoring 'part_' files"""
    list_of_files = glob.glob(f"{BASE_DIR}/*.pdf")
    # Filter out the individual 'part_' chunks so we don't try to split a split
    potential_masters = [f for f in list_of_files if "part_" not in os.path.basename(f).lower()]
    
    if not potential_masters:
        return None
    return max(potential_masters, key=os.path.getctime)

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def split_by_bookmarks(source_pdf):
    reader = PdfReader(source_pdf)
    bookmarks = reader.outline
    
    if not bookmarks:
        print("ℹ️ No internal bookmarks found in this PDF. Switching to manual mode.")
        return False

    print(f"📂 Found bookmarks in: {os.path.basename(source_pdf)}")
    
    for i, entry in enumerate(bookmarks):
        if isinstance(entry, list): continue # Skip nested sub-chapters for simplicity
        
        writer = PdfWriter()
        start_page = reader.get_destination_page_number(entry)
        
        # Determine end page based on the next bookmark or end of file
        if i + 1 < len(bookmarks) and not isinstance(bookmarks[i+1], list):
            end_page = reader.get_destination_page_number(bookmarks[i+1])
        else:
            end_page = len(reader.pages)
            
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
            
        chapter_title = sanitize_filename(entry.title)
        output_filename = f"Chapter_{i+1}_{chapter_title}.pdf"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"  ✅ Saved: {output_filename}")
    
    return True

def split_manually(source_pdf):
    reader = PdfReader(source_pdf)
    total_pages = len(reader.pages)
    print(f"📄 Source: {os.path.basename(source_pdf)} ({total_pages} pages)")
    
    ranges = input("Enter page ranges for chapters (e.g., 1-10, 11-25, 26-40): ")
    parts = ranges.split(",")
    
    for i, p_range in enumerate(parts):
        try:
            writer = PdfWriter()
            start, end = map(int, p_range.strip().split("-"))
            for page_num in range(start-1, min(end, total_pages)):
                writer.add_page(reader.pages[page_num])
            
            output_filename = f"Manual_Chapter_{i+1}.pdf"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            with open(output_path, "wb") as f:
                writer.write(f)
            print(f"  ✅ Saved: {output_filename}")
        except Exception as e:
            print(f"  ❌ Error on range {p_range}: {e}")

if __name__ == "__main__":
    latest_master = get_latest_pdf()
    
    if not latest_master:
        print(f"❌ No Master PDF found in {BASE_DIR}")
        print("Ensure you have run the stitcher first and the file is NOT named 'part_...'")
    else:
        print(f"🎯 Target identified: {os.path.basename(latest_master)}")
        if not split_by_bookmarks(latest_master):
            split_manually(latest_master)
        print(f"\n🚀 Done! Your chapters are ready in: {OUTPUT_DIR}")