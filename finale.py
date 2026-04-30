import cv2
import pytesseract
import numpy as np
import re
import os
import time
import io
import pyautogui
import pygetwindow as gw
import win32clipboard
from PIL import Image, ImageDraw, ImageFont
import mediapipe as mp
import webbrowser  # For auto-opening WhatsApp Web

# ⚠️ UNCOMMENT IF TESSERACT ISN'T IN SYSTEM PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ─────────────────────────────────────────────────────────────
# 1. SAFE CASCADE LOADING (Local XML + Fallback)
# ─────────────────────────────────────────────────────────────
def load_cascades():
    """Loads Haar cascades from local folder or OpenCV data"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Face detector
    face_local = os.path.join(base_dir, "haarcascade_frontalface_default.xml")
    if os.path.exists(face_local):
        face_cascade = cv2.CascadeClassifier(face_local)
    else:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Smile detector
    smile_local = os.path.join(base_dir, "haarcascade_smile.xml")
    if os.path.exists(smile_local):
        smile_cascade = cv2.CascadeClassifier(smile_local)
    else:
        smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
    
    # Verify
    if face_cascade.empty() or smile_cascade.empty():
        print("❌ CRITICAL: Haar cascade files not found!")
        print("💡 Download these files and place them in the same folder as finale.py:")
        print("   - haarcascade_frontalface_default.xml")
        print("   - haarcascade_smile.xml")
        print("🔗 Links: https://github.com/opencv/opencv/tree/master/data/haarcascades")
        exit(1)
    
    return face_cascade, smile_cascade

# ─────────────────────────────────────────────────────────────
# 2. OCR & PREPROCESSING
# ─────────────────────────────────────────────────────────────
def preprocess_for_tesseract(roi):
    """Advanced preprocessing pipeline for busy/colored IDs"""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    # Upscale for better OCR accuracy
    if h * 3.0 < 800 or w * 3.0 < 800:
        gray = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    # CLAHE for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    # Denoise to remove paper texture
    gray = cv2.fastNlMeansDenoising(gray, h=11, templateWindowSize=7, searchWindowSize=21)
    # Adaptive threshold for colored backgrounds
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 15, 10)
    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

def extract_name_and_phone(raw_text):
    """Smart parser to extract Name & Phone from messy OCR output"""
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    name, phone = None, None
    for line in lines:
        low = line.lower()
        # 📞 Phone extraction (Indian mobile: starts with 6-9, exactly 10 digits)
        if any(k in low for k in ['phone', 'mobile', 'contact', 'tel', 'no', 'number']):
            digits = re.sub(r'[^0-9]', '', line)
            match = re.search(r'[6-9]\d{9}', digits)
            if match: phone = match.group()
        # 👤 Name extraction (keyword-based + cleanup)
        if any(k in low for k in ['name', 'student', 'candidate', 'applicant', 'full name']):
            val = re.sub(r'^(name|student name|candidate|applicant|full name)[:.\s\-]*', '', line, flags=re.IGNORECASE)
            val = re.sub(r'[^A-Za-z\s\-\.]', '', val).strip()
            if len(val) > 1: name = val.title()
    return name or "Not Found", phone or "Not Found"

# ─────────────────────────────────────────────────────────────
# 3. BANNER & RECEIPT GENERATION
# ─────────────────────────────────────────────────────────────
def ensure_banner():
    """Creates banner template if it doesn't exist"""
    path = "banner_template.png"
    if not os.path.exists(path):
        img = Image.new("RGB", (1080, 1080), "#FFFFFF")
        draw = ImageDraw.Draw(img)
        draw.rectangle([340, 160, 740, 560], outline="#CCCCCC", width=4)
        try: font = ImageFont.truetype("arial.ttf", 30)
        except: font = ImageFont.load_default()
        draw.text((420, 345), "PHOTO AREA", fill="#999999", font=font)
        img.save(path)
    return path

def process_photo_to_banner(frame_bgr, banner_path, voter_name, box_coords=(340, 160, 740, 560)):
    """Pastes captured photo into banner template and adds voter name"""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w = frame_rgb.shape[:2]
    # Crop center square to avoid stretching
    size = min(h, w)
    square = frame_rgb[(h-size)//2:(h-size)//2+size, (w-size)//2:(w-size)//2+size]
    box_w, box_h = box_coords[2]-box_coords[0], box_coords[3]-box_coords[1]
    photo_pil = Image.fromarray(square).resize((box_w, box_h), Image.LANCZOS).convert("RGB")
    
    template = Image.open(banner_path).convert("RGB")
    if template.size != (1080, 1080): template = template.resize((1080, 1080), Image.LANCZOS)
    template.paste(photo_pil, (box_coords[0], box_coords[1]))
    
    # Add voter name to footer
    draw = ImageDraw.Draw(template)
    try: font = ImageFont.truetype("arial.ttf", 28)
    except: font = ImageFont.load_default()
    draw.text((400, 960), f"{voter_name.upper()} | THANK YOU FOR VOTING!", fill="#1D4ED8", font=font)
    
    out_name = f"receipt_{voter_name}_{int(time.time())}.png"
    template.save(out_name, optimize=True, quality=95)
    return out_name

# ─────────────────────────────────────────────────────────────
# 4. WHATSAPP SENDER (With Auto-Open Fallback)
# ─────────────────────────────────────────────────────────────
def copy_to_clipboard(image_path):
    """Copies image to Windows clipboard for pasting"""
    try:
        img = Image.open(image_path).convert("RGB")
        output = io.BytesIO()
        img.save(output, "BMP")
        data = output.getvalue()[14:]  # Strip BMP header
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except Exception as e:
        print(f"❌ Clipboard failed: {e}")
        return False

def send_via_whatsapp(phone, img_path):
    """Automates WhatsApp Web to send receipt image"""
    print("🌐 Preparing WhatsApp send...")
    try:
        # Check if WhatsApp is already open
        wins = gw.getWindowsWithTitle("WhatsApp")
        
        # If not found, open it automatically
        if not wins:
            print("🌐 WhatsApp not found. Opening web.whatsapp.com...")
            webbrowser.open('https://web.whatsapp.com')
            time.sleep(15)  # Wait for browser to load
            wins = gw.getWindowsWithTitle("WhatsApp")
            
        # Fallback: ask user if still not found
        if not wins:
             print("⚠️ Please open WhatsApp Web manually in your browser.")
             input("👉 Press ENTER once WhatsApp is visible...")
             wins = gw.getWindowsWithTitle("WhatsApp")

        if not wins:
             print("❌ Still couldn't find WhatsApp. Sending cancelled.")
             return False

        # Focus the window
        win = wins[-1]
        if not win.isActive: 
            win.activate()
        time.sleep(2)
        
        # Ensure focus on chat area
        pyautogui.click(x=win.width//2, y=win.height//2)
        time.sleep(0.5)

        print("🔍 Opening new chat (Ctrl+N)...")
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(2.5)

        print("🔢 Entering number...")
        pyautogui.write(phone, interval=0.06)
        time.sleep(2.5)
        pyautogui.press('enter')
        time.sleep(3.5)  # Wait for chat to fully initialize

        print("📋 Pasting receipt...")
        copy_to_clipboard(img_path)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(4.5)  # Wait for image to upload

        print("📤 Sending...")
        pyautogui.press('enter')
        print("✅ SENT SUCCESSFULLY! Check your phone.")
        return True
    except Exception as e:
        print(f"❌ WhatsApp Error: {e}")
        print("💡 Fallback: Manually send: " + os.path.abspath(img_path))
        return False

# ─────────────────────────────────────────────────────────────
# 5. MAIN WORKFLOW
# ─────────────────────────────────────────────────────────────
def main():
    print("🗳️ AUTOMATED VOTING SYSTEM - MASTER SCRIPT")
    print("="*60)
    
    # ─── PHASE 1: ID SCAN & OCR ───
    print("\n📷 PHASE 1: ID SCANNING")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): print("❌ Camera not found."); return
    state, processed_preview, raw_ocr = "READY", None, ""
    
    print("📄 Center ID in green box → SPACE = Capture → ENTER = Process → ESC = Quit")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        h, w, _ = frame.shape
        x1, y1, x2, y2 = int(w*0.2), int(h*0.2), int(w*0.8), int(h*0.8)
        display = frame.copy()
        
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 3)
        focus = cv2.Laplacian(cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        if focus < 120: cv2.putText(display, "⚠️ HOLD STEADY", (w//2-120, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        cv2.putText(display, f"STATE: {state}", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow("PHASE 1: ID Scan", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27: cap.release(); cv2.destroyAllWindows(); return
        
        if key == 32 and state == "READY" and focus > 120:
            state = "PREVIEW"
            processed_preview = preprocess_for_tesseract(frame[y1:y2, x1:x2])
        elif state == "PREVIEW":
            bordered = cv2.copyMakeBorder(processed_preview, 20, 60, 20, 20, cv2.BORDER_CONSTANT, value=0)
            cv2.putText(bordered, "✅ ENTER=Run OCR | SPACE=Retake", (30, bordered.shape[0]+50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.imshow("PHASE 1: ID Scan", bordered)
            if key == 13:
                cv2.imwrite("_temp_ocr.png", processed_preview)
                raw_ocr = pytesseract.image_to_string("_temp_ocr.png", config='--psm 6 --oem 1')
                if os.path.exists("_temp_ocr.png"): os.remove("_temp_ocr.png")
                break
            elif key == 32: state = "READY"
    cap.release(); cv2.destroyAllWindows()

    # ─── MANUAL REVIEW & CORRECTION ───
    print("\n📝 PHASE 1.5: REVIEW & CORRECTION")
    ext_name, ext_phone = extract_name_and_phone(raw_ocr)
    print(f"🔍 OCR Extracted: Name='{ext_name}' | Phone='{ext_phone}'")
    final_name = input("✅ Correct Name? (Enter to keep or type new): ").strip() or ext_name
    final_phone = input("✅ Correct Phone? (Enter to keep or type new): ").strip() or ext_phone
    print(f"💾 Final: {final_name} | +91{final_phone}\n")

    # ─── PHASE 2: SIMULATED INK APPLICATION ───
    print("☝️ PHASE 2: APPLYING VOTING INK")
    cap = cv2.VideoCapture(0)
    for i in range(1, 6):
        ret, frame = cap.read()
        if not ret: break
        h, w, _ = frame.shape
        cv2.rectangle(frame, (0, h-50), (w, h), (0,0,0), -1)
        cv2.rectangle(frame, (w//4, h-30), (w//4 + i*(w//3), h-10), (0, 255, 0), -1)
        cv2.putText(frame, f"APPLYING INK... {i*20}%", (w//2-100, h-60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.imshow("PHASE 2: Ink", frame)
        cv2.waitKey(600)
    cap.release(); cv2.destroyAllWindows()
    print("✅ Ink applied!\n")

    # ─── PHASE 3: FACE + FINGER + SMILE CAPTURE ───
    print("📷 PHASE 3: PHOTO CAPTURE")
    print("Loading detectors...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): print("❌ Camera failed."); return
    
    face_cascade, smile_cascade = load_cascades()
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
    banner_path = ensure_banner()
    
    state = "WAITING"
    temp_capture = None
    trigger_count = 0
    TRIGGER_THRESHOLD = 3  # Debounce: requires 3 consecutive frames
    
    print("Show Face + ☝️ Index Finger + 😊 Smile")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None: continue
        
        frame = cv2.flip(frame, 1)  # Mirror for natural preview
        clean_frame = frame.copy()  # Keep clean copy for saving
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 👆 Finger detection (MediaPipe)
        finger_raised = False
        try:
            res = hands.process(rgb)
            if res.multi_hand_landmarks:
                for hand in res.multi_hand_landmarks:
                    if hand.landmark[8].y < hand.landmark[6].y:  # Index tip above PIP
                        finger_raised = True; break
        except: pass

        # 😊 Face & Smile detection (Haar Cascades)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        smiling = False
        for (x, y, fw, fh) in faces:
            try:
                if len(smile_cascade.detectMultiScale(gray[y:y+fh, x:x+fw], 1.8, 10)) > 0:
                    smiling = True; break
            except: pass

        # State logic
        if state == "WAITING":
            if finger_raised and smiling: trigger_count += 1
            else: trigger_count = 0

            color = (0, 255, 0) if trigger_count > 0 else (0, 0, 255)
            txt = f"TRIGGERING... {trigger_count}/{TRIGGER_THRESHOLD}" if trigger_count > 0 else "Face + ☝️ + 😊"
            cv2.putText(frame, f"STATUS: {txt}", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.imshow("PHASE 3: Capture", frame)
            
            if trigger_count >= TRIGGER_THRESHOLD:
                temp_capture = clean_frame.copy()
                state = "PREVIEW"
                trigger_count = 0
                print("📸 Frame frozen! Press SPACE to confirm.")
                
        elif state == "PREVIEW":
            if temp_capture is None or temp_capture.size == 0:
                state = "WAITING"; continue
            cv2.rectangle(temp_capture, (0, temp_capture.shape[0]-50), (temp_capture.shape[1], temp_capture.shape[0]), (0,0,0), -1)
            cv2.putText(temp_capture, "SPACE=Confirm | ESC=Retry", (20, temp_capture.shape[0]-15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
            cv2.imshow("PHASE 3: Capture", temp_capture)

        # 🔑 CRITICAL: Exactly ONE waitKey per frame to prevent freeze
        key = cv2.waitKey(1) & 0xFF
        if key == 32 and state == "PREVIEW":
            try:
                receipt = process_photo_to_banner(temp_capture, banner_path, final_name)
                print(f"💾 Receipt saved: {receipt}")
                cap.release(); cv2.destroyAllWindows()
                break
            except Exception as e:
                print(f"💥 Banner Error: {e}"); state = "WAITING"
        elif key == 27 and state == "PREVIEW": state = "WAITING"; trigger_count = 0
        elif key == 27: cap.release(); cv2.destroyAllWindows(); return

    # ─── PHASE 4: WHATSAPP SEND ───
    print(f"\n📱 PHASE 4: SENDING TO +91{final_phone}")
    receipt_files = [f for f in os.listdir() if f.startswith("receipt_") and f.endswith(".png")]
    receipt_path = max(receipt_files, key=os.path.getctime) if receipt_files else None
    
    if receipt_path: send_via_whatsapp(final_phone, receipt_path)
    else: print("❌ Receipt file missing.")
        
    print("\n🏁 VOTING SESSION COMPLETE.")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n👋 Interrupted.")
    except Exception as e: print(f"💥 Critical Error: {e}")
