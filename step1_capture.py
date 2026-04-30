import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import time

# ─────────────────────────────────────────────────────────────
# 1. SETUP DETECTORS
# ─────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

# ─────────────────────────────────────────────────────────────
# 2. AUTO-GENERATE BANNER
# ─────────────────────────────────────────────────────────────
def ensure_banner():
    path = "banner_template.png"
    if not os.path.exists(path):
        print("🎨 Creating banner_template.png...")
        img = Image.new("RGB", (1080, 1080), "#FFFFFF")
        draw = ImageDraw.Draw(img)
        draw.rectangle([340, 160, 740, 560], outline="#CCCCCC", width=4)
        try: font = ImageFont.truetype("arial.ttf", 30)
        except: font = ImageFont.load_default()
        draw.text((420, 345), "PHOTO AREA", fill="#999999", font=font)
        img.save(path)
    return path

# ─────────────────────────────────────────────────────────────
# 3. DETECTION HELPERS
# ─────────────────────────────────────────────────────────────
def is_finger_raised(hand_landmarks):
    return hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y

def check_smile(frame, face_rect):
    x, y, w, h = face_rect
    roi_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
    return len(smile_cascade.detectMultiScale(roi_gray, 1.8, 15)) > 0

# ─────────────────────────────────────────────────────────────
# 4. SAFE PHOTO PROCESSING (Clean frame, no overlays)
# ─────────────────────────────────────────────────────────────
def process_photo_to_banner(frame_bgr, banner_path, box_coords=(340, 160, 740, 560)):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w = frame_rgb.shape[:2]
    size = min(h, w)
    x_crop, y_crop = (w - size) // 2, (h - size) // 2
    square = frame_rgb[y_crop:y_crop+size, x_crop:x_crop+size]
    
    box_w = box_coords[2] - box_coords[0]
    box_h = box_coords[3] - box_coords[1]
    photo_pil = Image.fromarray(square).resize((box_w, box_h), Image.LANCZOS).convert("RGB")
    
    template = Image.open(banner_path).convert("RGB")
    if template.size != (1080, 1080):
        template = template.resize((1080, 1080), Image.LANCZOS)
        
    template.paste(photo_pil, (box_coords[0], box_coords[1]))
    out_name = f"receipt_{int(time.time())}.png"
    template.save(out_name, optimize=True, quality=95)
    return out_name

# ─────────────────────────────────────────────────────────────
# 5. MAIN LOOP (State Machine: WAITING -> PREVIEW -> DONE)
# ─────────────────────────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not found. Check USB permissions.")
        return

    banner_path = ensure_banner()
    print("📷 READY! Show Face + ☝️ Index Finger + 😊 Smile")
    print("📂 Clean receipts save in: " + os.getcwd())

    state = "WAITING"
    temp_capture = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Camera read failed")
            break

        frame = cv2.flip(frame, 1)
        clean_frame = frame.copy()  # 🔑 Pristine copy for saving
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 👆 HAND CHECK
        finger_raised = False
        results = hands.process(rgb_frame)
        if results.multi_hand_landmarks:
            for hand in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                if is_finger_raised(hand):
                    finger_raised = True
                    break

        # 😊 FACE & SMILE CHECK
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        smiling = False
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            if check_smile(frame, (x, y, w, h)):
                smiling = True

        # 🟢 STATE LOGIC
        all_met = finger_raised and smiling

        if state == "WAITING":
            status_color = (0, 255, 0) if all_met else (0, 0, 255)
            status_text = "WAITING: Face + ☝️ Finger + 😊 Smile" if not all_met else "✅ TRIGGERED!"
            cv2.putText(frame, status_text, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            cv2.imshow("Voting System", frame)

            if all_met:
                temp_capture = clean_frame.copy()
                state = "PREVIEW"
                print("📸 Capture frozen! Keep window focused.")
                print("⌨️ SPACE = Confirm & Save | ESC = Retry")

        elif state == "PREVIEW":
            # Show clean capture with prompt
            display_frame = temp_capture.copy()
            h, w = display_frame.shape[:2]
            cv2.rectangle(display_frame, (0, h-80), (w, h), (0, 0, 0), -1)
            cv2.putText(display_frame, "SPACE = Confirm  |  ESC = Retry", (20, h-30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.imshow("Voting System", display_frame)

            key = cv2.waitKey(1) & 0xFF  # Non-blocking key check
            if key == 32:  # SPACE
                print("✅ Confirmed. Generating receipt...")
                out_name = process_photo_to_banner(temp_capture, banner_path)
                print(f"💾 Saved: {os.path.join(os.getcwd(), out_name)}")
                state = "DONE"
            elif key == 27:  # ESC
                print("🔄 Retrying... Pose again.")
                state = "WAITING"
                temp_capture = None

        elif state == "DONE":
            frame = cv2.flip(cap.read()[1], 1) if cap.isOpened() else np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "✅ RECEIPT GENERATED! Closing in 3s...", (80, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Voting System", frame)
            cv2.waitKey(3000)
            break

        if cv2.waitKey(1) & 0xFF == 27 and state == "WAITING":
            break

    cap.release()
    cv2.destroyAllWindows()
    print("👋 Session ended.")

if __name__ == "__main__":
    main()