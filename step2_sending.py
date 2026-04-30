import os
import glob
import sys
import time
import io
import pyautogui
import pygetwindow as gw
import win32clipboard
from PIL import Image

# ─────────────────────────────────────────────────────────────
# 1. COPY IMAGE TO CLIPBOARD
# ─────────────────────────────────────────────────────────────
def copy_to_clipboard(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        output = io.BytesIO()
        img.save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"❌ Clipboard failed: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# 2. FOCUS EXISTING WHATSAPP TAB (NO URL CHANGE)
# ─────────────────────────────────────────────────────────────
def focus_whatsapp_window():
    wins = gw.getWindowsWithTitle("WhatsApp")
    if not wins:
        print("❌ WhatsApp Web tab not found. Open it manually first.")
        sys.exit(1)
        
    win = wins[-1]  # Grab most recent
    print("✅ Found WhatsApp window. Focusing...")
    if not win.isActive:
        win.activate()
    time.sleep(1)
    return win

# ─────────────────────────────────────────────────────────────
# 3. MAIN FLOW
# ─────────────────────────────────────────────────────────────
def get_latest_receipt():
    files = glob.glob("receipt_*.png")
    return max(files, key=os.path.getctime) if files else None

def main():
    print("🚀 STEP 2: Smart WhatsApp Sender (No Reload)")
    print("="*45)
    
    img = get_latest_receipt()
    if not img:
        print("❌ No receipt found. Run Step 1 first.")
        sys.exit(1)
        
    phone = input("📞 Phone (e.g., 919309268898): ").strip()
    if not phone.isdigit():
        print("❌ Invalid number."); sys.exit(1)

    # 1. Focus tab
    focus_whatsapp_window()
    time.sleep(1)
    
    # 2. Open New Chat (Ctrl+Alt+N works on WA Web desktop & web)
    print("🔍 Opening new chat...")
    pyautogui.hotkey('ctrl', 'alt', 'n')
    time.sleep(1.5)
    
    # 3. Type number in search box
    print("🔢 Entering phone number...")
    pyautogui.write(phone, interval=0.05)
    time.sleep(1.5)
    
    # 4. Press Enter to select chat
    pyautogui.press('enter')
    time.sleep(2)
    
    # 5. Copy & Paste Image
    print("📋 Pasting image...")
    copy_to_clipboard(img)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(2)  # Wait for thumbnail to load
    
    # 6. Send
    pyautogui.press('enter')
    print("✅ SENT SUCCESSFULLY! Check your phone.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Aborted.")