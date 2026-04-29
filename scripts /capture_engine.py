import os
import time
import pyautogui
import img2pdf
from pynput import keyboard

# --- 1. STACK CONFIGURATION ---
DRIVE_FOLDER = r"/Users/sameoldexpressions/Library/CloudStorage/GoogleDrive-alex.e.yedi@gmail.com/My Drive/(Owned) Professional /Percy Pro-Jays/scrreennshots"
TEMP_DIR = os.path.expanduser("~/Documents/temp_captures")

# Ensure Infrastructure exists
os.makedirs(TEMP_DIR, exist_ok=True)
if not os.path.exists(DRIVE_FOLDER):
    print(f"❌ DRIVE ERROR: Folder not found. Check if Google Drive app is running.")
    exit()

captured_pages = []

print(f"🚀 ENGINE START: Saving to 'scrreennshots'")
print(f"1. Open your document.")
print(f"2. Tap 'A' to capture the current frame.")
print(f"3. Tap 'ESC' to stitch & sync.")

# --- 2. UPDATED CAPTURE LOGIC ---
def on_press(key):
    try:
        # Listen specifically for the lowercase 'a' key
        if key.char == 'a':
            ts = time.strftime("%H%M%S%f")
            path = os.path.join(TEMP_DIR, f"p_{ts}.png")
            
            # Capture
            pyautogui.screenshot().save(path)
            captured_pages.append(path)
            print(f"📸 Captured Page {len(captured_pages)}")
            
    except AttributeError:
        # This handles non-character keys (like shift, ctrl, etc.) so the script doesn't crash
        pass
    except Exception as e:
        print(f"⚠️ Capture Error: {e}")

# --- 3. STITCH & SYNC LOGIC ---
def on_release(key):
    if key == keyboard.Key.esc:
        if captured_pages:
            final_name = f"Research_Capture_{time.strftime('%Y%m%d_%H%M')}.pdf"
            dest = os.path.join(DRIVE_FOLDER, final_name)
            
            print(f"\n📦 Stitching {len(captured_pages)} pages into {final_name}...")
            captured_pages.sort()
            
            try:
                with open(dest, "wb") as f:
                    f.write(img2pdf.convert(captured_pages))
                
                print(f"✅ VAULTED: {final_name}")
                # Cleanup
                for p in captured_pages: os.remove(p)
                print(f"🗑️ Temporary images cleared.")
            except Exception as e:
                print(f"Stitching/Saving Error: {e}")
        else:
            print("No pages were captured. Exiting.")
            
        return False # Stops the listener

# --- 4. START ---
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()