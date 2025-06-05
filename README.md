
# 🎬 Video Labeling Web App (MVP)

This is a minimal, fast, and easy-to-use **local web app** for labeling `.mp4` videos with custom tags. It’s designed for researchers, ML practitioners, and data engineers who need to sort and annotate a set of videos using metadata and store the labels in a structured way.

Built with **Streamlit** and **pandas**, the app supports smooth video playback, CSV metadata display, and one-hot encoded label editing — all with keyboard shortcuts for efficient annotation.

---

## 🚀 Features

- ✅ Load and preview short `.mp4` videos from a local folder
- ✅ Load external metadata (`metadata.csv`) and match by filename
- ✅ Display metadata alongside the video
- ✅ Add or select **custom labels** — stored as one-hot columns in the same CSV
- ✅ Previous / Next navigation through videos
- ✅ Sort videos by name or any metadata column
- ✅ Auto-save label updates
- ✅ Progress indicator (e.g. "Video 12 of 300")
- ✅ Keyboard shortcuts for labeling and navigation

---

## 🗂 Folder Structure

```

video\_labeler/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
└── README.md               # You're reading it

folder with videos/
├── video1.mp4
└── ...
├── metadata.csv            # CSV with metadata and label columns

````

---

## 🧾 `metadata.csv` Format

Your CSV must include at least a `filename` column, matching each video’s filename exactly.

Example:

```csv
filename,duration,source,age
video1.mp4,3.5,webcam,25
video2.mp4,2.9,upload,42
````

After labeling, the CSV will be auto-extended with one-hot label columns:

```csv
filename,duration,source,age,funny,blurry,suspicious
video1.mp4,3.5,webcam,25,1,0,0
video2.mp4,2.9,upload,42,0,0,1
```

---

## 🛠 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/video-labeler.git
cd video-labeler
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run the App

```bash
streamlit run app.py
```

It will launch in your browser at `http://localhost:8501`.

---

## ⌨️ Keyboard Shortcuts

| Action         | Shortcut       |
| -------------- | -------------- |
| Add new label  | Type + Enter   |
| Toggle label   | Click or key   |
| Next video     | Right arrow →  |
| Previous video | Left arrow ←   |
| Save label     | Auto on toggle |

(More shortcuts can be added in `app.py` using Streamlit keyboard event hacks or JS injection.)

---

## 📋 TODO / Future Work

* [ ] Add search/filter for labels
* [ ] Add multi-user support or session tracking
* [ ] Export labeled data as JSON or separate file
* [ ] Optional cloud backup (e.g. GCS sync)

---

## 📄 License

MIT License. Use freely with credit.

---
