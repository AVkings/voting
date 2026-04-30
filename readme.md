# 🗳️ Automated Voting System Prototype

A Python-based prototype that automates the voter verification, photo capture, and digital receipt workflow. Designed for school/college elections or demo environments, it chains OCR, biometric-style triggers, and UI automation into a seamless pipeline.

## ✨ Features
- **📷 Phase 1: ID Scanning & OCR** – Extracts `Name` and `Phone` directly from printed ID cards using advanced image preprocessing.
- **📝 Phase 1.5: Manual Review** – Console prompt lets you correct OCR errors before proceeding.
- **☝️ Phase 2: Simulated Ink Application** – Visual progress bar mimics the traditional indelible ink step.
- **🖼️ Phase 3: Smart Photo Capture** – Uses MediaPipe (hand tracking) + OpenCV (face/smile detection) to trigger a clean capture only when Face + Index Finger + Smile are detected.
- **🎨 Phase 4: Receipt Generation & WhatsApp Send** – Auto-generates a personalized banner receipt and sends it via WhatsApp Web using clipboard automation & UI shortcuts.

## 🛠️ Tech Stack
| Component | Library/Tool |
|-----------|--------------|
| Camera & CV | `OpenCV`, `MediaPipe` |
| OCR Engine | `Tesseract OCR` + `pytesseract` |
| UI Automation | `PyAutoGUI`, `PyGetWindow`, `PyWin32` |
| Image Processing | `Pillow`, `NumPy` |
| OS Target | Windows 10/11 (clipboard & window APIs) |

## 📦 Installation

### 1. Clone & Setup Environment
```bash
git clone https://github.com/AVkings/voting.git
cd voting
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
