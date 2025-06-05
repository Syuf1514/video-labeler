# 🎬 Video Labeling Web App (MVP)

This project provides a tiny Streamlit app for quickly tagging small `.mp4` videos with custom labels. Videos and a `metadata.csv` file live inside a folder you choose. The app loads that CSV, shows each video with its metadata and lets you add or toggle labels. All label changes are saved back to the same CSV immediately.

---

## Features

- Load and preview videos from any local folder
- Read external metadata (`metadata.csv`) matched by `filename`
- Display all metadata fields next to the video
- Create new labels on the fly and store them as one‑hot columns
- Previous/Next navigation with buttons or arrow‑key shortcuts
- Toggle labels with checkboxes or number keys (1‑9)
- Auto‑save after every change
- Progress indicator ("Video X of N")
- Sort videos by filename or any other column

---

## Folder Layout

```
video-labeler/
├── app.py            # Streamlit application
├── requirements.txt  # Dependencies
├── README.md         # This file
└── sample_videos/
    ├── <your .mp4 files>
    └── metadata.csv
```

`metadata.csv` must contain a `filename` column that matches the video files. Any additional columns are treated as metadata, except for integer columns containing only 0/1 which are interpreted as labels.

Example `metadata.csv`:

```csv
filename,duration,source
video1.mp4,1.0,generator
video2.mp4,1.0,generator
```

After labeling, the CSV will look like:

```csv
filename,duration,source,funny,blurry
video1.mp4,1.0,generator,1,0
video2.mp4,1.0,generator,0,1
```

---

## Installation

```bash
pip install -r requirements.txt
```

(Using a virtual environment is recommended.)

---

## Running

```bash
streamlit run app.py
```

Open <http://localhost:8501> in your browser. The sidebar lets you select the video folder (default is `sample_videos`).

### Keyboard shortcuts

- **Right / Left arrows** – next or previous video
- **1‑9** – toggle the corresponding label checkbox
- **Type a label name** in the input box and press **Add Label** to create a new one

Make sure the page has focus (click anywhere on the page) so the keys are captured.

---

## License

MIT
