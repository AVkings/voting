# 🗳️ Automated Voting System Prototype

A Python-based prototype that automates voter verification, photo capture, and digital receipt delivery via WhatsApp.


![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green?style=flat&logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-HandTracking-orange?style=flat)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)


## ✨ Features

| Phase | Feature | Description |
|-------|---------|-------------|
| 📷 **Phase 1** | ID Scanning & OCR | Extracts `Name` and `Phone` from printed IDs using advanced preprocessing (CLAHE, denoising, adaptive threshold) |
| 📝 **Phase 1.5** | Manual Review | Console prompt to correct OCR errors before proceeding |
| ☝️ **Phase 2** | Simulated Ink Application | Visual progress bar mimics traditional indelible ink step |
| 🖼️ **Phase 3** | Smart Photo Capture | MediaPipe hand tracking + OpenCV face/smile detection triggers capture only when Face + ☝️ Finger + 😊 Smile detected |
| 🎨 **Phase 4** | Receipt & WhatsApp Send | Auto-generates personalized banner receipt and sends via WhatsApp Web using clipboard automation |

---

## 🛠️ Tech Stack

| Component | Library/Tool | Purpose |
|-----------|--------------|---------|
| **Camera & CV** | `OpenCV`, `MediaPipe` | Face detection, hand tracking, image preprocessing |
| **OCR Engine** | `Tesseract OCR` + `pytesseract` | Text extraction from ID cards |
| **UI Automation** | `PyAutoGUI`, `PyGetWindow`, `PyWin32` | WhatsApp Web automation, window management |
| **Image Processing** | `Pillow`, `NumPy` | Banner generation, image manipulation |
| **OS Target** | Windows 10/11 | Clipboard & window APIs |

---

## 📦 Installation

### Step 1: Clone & Setup Environment
```bash
git clone https://github.com/AVkings/voting.git
cd voting
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
opencv-contrib-python>=4.8.0
pytesseract>=0.3.10
mediapipe>=0.10.0
pyautogui>=0.9.54
pygetwindow>=0.0.9
pywin32>=306
pillow>=10.0.0
numpy>=1.24.0,<2.0
```

> ⚠️ **Important**: NumPy must be `<2.0` for compatibility with OpenCV/MediaPipe.

---

## 🔤 Tesseract OCR Installation (REQUIRED)

This project uses **Tesseract OCR** for text extraction. You must install it separately — it's not a Python package.

### 🪟 Windows
1. **Download installer**: https://github.com/UB-Mannheim/tesseract/wiki
2. Run `tesseract-ocr-w64-setup-5.x.x.exe`
3. ✅ Check **"Additional language data"** → Select **English**
4. Keep default path: `C:\Program Files\Tesseract-OCR`
5. **Add to PATH** (if not auto-added):
   - Search "Environment Variables" → Edit `Path` → Add `C:\Program Files\Tesseract-OCR`
6. Verify:
   ```cmd
   tesseract --version
   ```

### 🍎 macOS
```bash
brew install tesseract
brew install tesseract-lang  # Optional: additional languages
```

### 🐧 Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng libtesseract-dev
```

### 🔧 Python Configuration
If Tesseract isn't in your system PATH, uncomment this line at the top of `finale.py`:
```python
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 🚀 Usage

### 1. Prepare WhatsApp Web
- Open Chrome/Edge → Go to [web.whatsapp.com](https://web.whatsapp.com)
- Log in and keep the tab **visible** (not minimized)

### 2. Run the System
```bash
python finale.py
```

### 3. Follow the Workflow
```
📷 PHASE 1: ID SCANNING
   → Center ID in green box
   → SPACE = Capture → ENTER = Process

📝 PHASE 1.5: REVIEW & CORRECTION  
   → Verify extracted Name/Phone
   → Type corrections if needed

☝️ PHASE 2: APPLYING VOTING INK
   → Watch simulated progress animation

🖼️ PHASE 3: PHOTO CAPTURE
   → Show Face + ☝️ Index Finger + 😊 Smile
   → System auto-triggers after 3 confirmed frames
   → SPACE = Confirm | ESC = Retry

🎨 PHASE 4: RECEIPT & WHATSAPP SEND
   → Receipt auto-generated with voter name
   → WhatsApp Web opens → sends receipt automatically
```

---

## 📁 Project Structure
```
voting/
├── finale.py                 # Main executable script
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── haarcascade_frontalface_default.xml  # Face detector (download)
├── haarcascade_smile.xml                # Smile detector (download)
├── banner_template.png       # Auto-generated receipt template
├── receipt_*.png            # Generated voting receipts
└── _temp_*.png              # Temporary OCR files (auto-cleaned)
```

### 🔗 Download Haar Cascade Files
Place these in the project folder for reliable detection:
- [haarcascade_frontalface_default.xml](https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml)
- [haarcascade_smile.xml](https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_smile.xml)

---

## ⚠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `cv2.error: !empty()` | Download Haar XML files and place in project folder |
| `TesseractNotFoundError` | Install Tesseract OCR + add to PATH (see above) |
| `numpy.core.multiarray failed` | Downgrade NumPy: `pip install "numpy<2.0"` |
| WhatsApp not sending | Ensure WhatsApp Web is open, logged in, and visible |
| Camera not detected | Check USB permissions, close other apps using camera |
| `.exe` flagged by antivirus | Add project folder to Windows Defender exclusions |

### 🦠 PyInstaller .exe Antivirus Warning
If building an executable:
```bash
# Add project folder to Windows Defender exclusions:
# Settings → Privacy & Security → Windows Security → Virus & threat protection → Manage settings → Exclusions → Add folder

Shows: ID scan → OCR extraction → Ink simulation → Biometric capture → WhatsApp receipt delivery.
```
---

## 🤝 Contributing
1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License
MIT License. Free to use, modify, and distribute for educational purposes.

---

## 👤 Author
**Avnish Rajurkar**  
🔗 GitHub: [@AVkings](https://github.com/AVkings)  
📧 Contact: [avkings604@gmail.com]

*Built for HackClub Flavor Town 2024 🌶️*

---

> ℹ️ **AI Disclosure**: This README was drafted with assistance from an AI language model to ensure clarity, completeness, and technical accuracy. All project code, architecture, and functionality were developed independently by the author. Final edits and verification were performed manually.

---

### ✅ Submission Checklist
- [x] Tesseract installation instructions included
- [x] All dependencies listed with version constraints  
- [x] Troubleshooting section for common errors
- [x] Haar cascade download links provided
- [x] AI disclosure statement added
- [x] Clear step-by-step usage guide
