import cv2
import pytesseract
import re
import numpy as np
import time
import os

# ⚠️ UNCOMMENT & UPDATE if Tesseract isn't in your system PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ─────────────────────────────────────────────────────────────
# 1. ADVANCED PREPROCESSING (6-Step Pipeline)
# ─────────────────────────────────────────────────────────────
def preprocess_for_tesseract(roi):
    """Maximizes text clarity for Tesseract on busy/colored IDs"""
    # 1️⃣ Grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # 2️⃣ Upscale to ~300 DPI equivalent (Tesseract hates small text)
    h, w = gray.shape
    scale_factor = 3.0  # 3x upscale ensures even small ID text is readable
    if h * scale_factor < 800 or w * scale_factor < 800:
        gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
        
    # 3️⃣ CLAHE: Boosts local contrast without blowing out highlights
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # 4️⃣ Denoise: Removes paper texture & background grain
    gray = cv2.fastNlMeansDenoising(gray, h=11, templateWindowSize=7, searchWindowSize=21)
    
    # 5️⃣ Adaptive Threshold: Crushes colored backgrounds/watermarks
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 15, 10)
                                   
    # 6️⃣ Morphological Cleanup: Closes gaps in letters, removes speckles
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
    
    return cleaned

# ─────────────────────────────────────────────────────────────
# 2. SMART FIELD PARSER (Regex + Heuristics)
# ─────────────────────────────────────────────────────────────
def extract_name_and_phone(raw_text):
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    name, phone = None, None

    for line in lines:
        low = line.lower()
        
        # 📞 PHONE: Match keywords, extract 10-digit Indian mobile
        if any(k in low for k in ['phone', 'mobile', 'contact', 'tel', 'no', 'number']):
            digits = re.sub(r'[^0-9]', '', line)
            match = re.search(r'[6-9]\d{9}', digits)
            if match: phone = match.group()
            
        # 👤 NAME: Match keywords, strip punctuation, keep alphabetic
        if any(k in low for k in ['name', 'student', 'candidate', 'applicant', 'full name']):
            val = re.sub(r'^(name|student name|candidate|applicant|full name)[:.\s\-]*', '', line, flags=re.IGNORECASE)
            val = re.sub(r'[^A-Za-z\s\-\.]', '', val).strip()
            if len(val) > 1: name = val.title()
            
    return name or "Not Found", phone or "Not Found"

# ─────────────────────────────────────────────────────────────
# 3. MAIN LOOP (Focus-Enforced, ROI-Targeted, Zero-Mirror)
# ─────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not found.")
        return

    print("📷 STEP 3: Max-Accuracy Local OCR")
    print("="*60)
    print("🎯 Guide: Center the ID so text falls INSIDE the green box")
    print("⌨️ SPACE = Capture ROI | ENTER = Run OCR | R = Retake | ESC = Quit")
    print("-"*60)

    state = "READY"
    processed_preview = None
    raw_ocr = ""

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 🔑 ZERO MIRROR: Raw feed goes straight to preview & OCR
        display = frame.copy()
        h, w, _ = display.shape

        # GUIDE BOX (Center 60% of frame)
        x1, y1 = int(w*0.2), int(h*0.2)
        x2, y2 = int(w*0.8), int(h*0.8)
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(display, "📄 CENTER TEXT HERE", (x1+10, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # FOCUS CHECK
        roi_blur = frame[y1:y2, x1:x2]
        gray_roi = cv2.cvtColor(roi_blur, cv2.COLOR_BGR2GRAY)
        focus_score = cv2.Laplacian(gray_roi, cv2.CV_64F).var()
        is_sharp = focus_score > 120
        
        if not is_sharp:
            cv2.putText(display, "⚠️ TOO BLURRY - HOLD STEADY", (w//2-180, h-30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

        # STATE UI
        cv2.putText(display, f"STATE: {state}", (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.imshow("Max-Accuracy OCR", display)
        key = cv2.waitKey(1) & 0xFF

        # ─── CAPTURE ROI ───
        if key == 32 and state == "READY" and is_sharp:
            print("📸 Capturing ROI...")
            roi = frame[y1:y2, x1:x2]
            processed_preview = preprocess_for_tesseract(roi)
            state = "PREVIEW"
            print("✅ ROI captured & preprocessed. Review window opened.")

        # ─── REVIEW PRE-PROCESSED IMAGE ───
        elif state == "PREVIEW":
            # Show exactly what Tesseract will read
            proc_h, proc_w = processed_preview.shape[:2]
            # Add black border for visibility
            bordered = cv2.copyMakeBorder(processed_preview, 20, 60, 20, 20, cv2.BORDER_CONSTANT, value=0)
            cv2.putText(bordered, "✅ Press ENTER to run OCR | SPACE/R to retake", (30, proc_h + 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("Max-Accuracy OCR", bordered)

            if key == 13:  # ENTER
                state = "PROCESSING"
                print("🔍 Running Tesseract...")
                # Save to temp file (Windows Tesseract reads files more reliably)
                TEMP_PATH = "_tesseract_input.png"
                cv2.imwrite(TEMP_PATH, processed_preview)
                
                raw_ocr = pytesseract.image_to_string(TEMP_PATH, config='--psm 6 --oem 1')
                ext_name, ext_phone = extract_name_and_phone(raw_ocr)
                
                print("\n" + "="*60)
                print("📊 EXTRACTION RESULT:")
                print(f"👤 Name : {ext_name}")
                print(f"📞 Phone: {ext_phone}")
                print(f"📝 Raw OCR: {raw_ocr[:120].replace(chr(10), ' | ')}...")
                print("="*60 + "\n")
                
                if os.path.exists(TEMP_PATH): os.remove(TEMP_PATH)
                time.sleep(2)
                state = "READY"
                
            elif key == 32 or key == ord('r'):
                state = "READY"
                print("🔄 Retaking... Adjust lighting/angle.")

        elif key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Scanner closed.")

if __name__ == "__main__":
    main()