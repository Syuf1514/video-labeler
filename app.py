import os
import json
import logging
import sys
import pandas as pd
import streamlit as st
import yaml
from st_keyup import st_keyup

st.set_page_config(layout="centered")

st.markdown(
    """
    <style>
    .block-container {padding-top: 0.5rem;}
    .stVideo video {height: 80vh;}
    </style>
    """,
    unsafe_allow_html=True,
)

LOG_PATH = "app.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


def log_exception(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))


sys.excepthook = log_exception

STATE_PATH = "state.json"

def load_state():
    data = {"idx": 0, "video_dir": "videos"}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH) as f:
                stored = json.load(f)
            data.update(stored)
        except Exception as e:
            logging.error("Failed to load state: %s", e)
    return data


def save_state():
    try:
        with open(STATE_PATH, "w") as f:
            json.dump({"idx": st.session_state.idx, "video_dir": st.session_state.video_dir}, f)
    except Exception as e:
        logging.error("Failed to save state: %s", e)


if "idx" not in st.session_state or "video_dir" not in st.session_state:
    saved = load_state()
    st.session_state.idx = saved.get("idx", 0)
    st.session_state.video_dir = saved.get("video_dir", "videos")

VIDEO_DIR = st.sidebar.text_input("Video folder", st.session_state.video_dir, key="video_dir")

if not os.path.isdir(VIDEO_DIR):
    st.error(f"Folder '{VIDEO_DIR}' not found")
    logging.error("Folder '%s' not found", VIDEO_DIR)
    st.stop()

CSV_PATH = os.path.join(VIDEO_DIR, "metadata.csv")
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error(f"metadata.csv not found in {VIDEO_DIR}")
    logging.error("metadata.csv not found in %s", VIDEO_DIR)
    st.stop()

# Determine label columns (int columns with only 0/1 values)
label_cols = [c for c in df.columns if pd.api.types.is_integer_dtype(df[c]) and df[c].dropna().isin([0, 1]).all()]

metadata_cols = [c for c in df.columns if c not in label_cols and c != "filename"]

sort_by = st.sidebar.selectbox("Sort videos by", df.columns.tolist(), index=df.columns.get_loc('filename'))
order = st.sidebar.radio("Order", ["Ascending", "Descending"], horizontal=True)

with st.sidebar.expander("Logs"):
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH) as f:
                lines = f.readlines()
            st.text("".join(lines[-20:]))
        except Exception as e:
            st.text(f"Failed to read log: {e}")

if sort_by:
    asc = order == "Ascending"
    df = df.sort_values(by=sort_by, ascending=asc).reset_index(drop=True)

video_files = df['filename'].tolist()

def save_df():
    try:
        df.to_csv(CSV_PATH, index=False)
    except Exception as e:
        logging.error("Failed to save CSV: %s", e)

# Navigation callbacks

def next_video():
    st.session_state.idx = (st.session_state.idx + 1) % len(df)
    save_state()
    logging.info("Moved to next video: %s", video_files[st.session_state.idx])

def prev_video():
    st.session_state.idx = (st.session_state.idx - 1) % len(df)
    save_state()
    logging.info("Moved to previous video: %s", video_files[st.session_state.idx])

# Capture keyboard
key = st_keyup("", key="nav", label_visibility="collapsed")
if key in ("ArrowRight", " "):
    next_video()
    logging.info("Next video via keyboard")
elif key == "ArrowLeft":
    prev_video()
    logging.info("Previous video via keyboard")
elif key.isdigit():
    n = int(key)
    if 1 <= n <= len(label_cols):
        col = label_cols[n-1]
        df.loc[st.session_state.idx, col] = 1 - df.loc[st.session_state.idx, col]
        st.session_state[f"lbl_{col}_{st.session_state.idx}"] = bool(df.loc[st.session_state.idx, col])
        save_df()
        current_file = video_files[st.session_state.idx]
        logging.info("Toggled label %s for video %s via keyboard", col, current_file)

current_file = video_files[st.session_state.idx]
st.markdown(
    f"<div style='text-align:right;color:gray'>{st.session_state.idx + 1}/{len(video_files)}</div>",
    unsafe_allow_html=True,
)
video_path = os.path.join(VIDEO_DIR, current_file)

video_col, meta_col = st.columns([3, 2])

with video_col:
    if os.path.exists(video_path):
        video_bytes = open(video_path, 'rb').read()
        st.video(video_bytes, autoplay=True, muted=False)
    else:
        st.warning(f"Video file '{current_file}' not found")
        logging.error("Video file '%s' not found", current_file)

    st.caption(current_file)

    def toggle_label(col):
        val = st.session_state[f"lbl_{col}_{st.session_state.idx}"]
        df.loc[st.session_state.idx, col] = int(val)
        save_df()
        logging.info("Toggled label %s for video %s", col, current_file)

    for i, col in enumerate(label_cols):
        default = bool(df.loc[st.session_state.idx, col])
        key = f"lbl_{col}_{st.session_state.idx}"
        st.checkbox(
            f"{i+1}. {col}",
            value=default,
            key=key,
            on_change=toggle_label,
            args=(col,),
        )

    new_label = st.text_input("Add new label")
    if st.button("Add Label") and new_label:
        if new_label not in df.columns:
            df[new_label] = 0
            label_cols.append(new_label)
            df.loc[st.session_state.idx, new_label] = 1
            st.session_state[f"lbl_{new_label}_{st.session_state.idx}"] = True
            save_df()
            st.experimental_rerun()

    nav1, nav2 = st.columns(2)
    with nav1:
        st.button("◀ Previous", on_click=prev_video, key="prev")
    with nav2:
        st.button("Next ▶", on_click=next_video, key="next")

with meta_col:
    st.caption("Metadata")
    metadata = df.loc[st.session_state.idx, metadata_cols].to_dict()
    yaml_text = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    st.code(yaml_text, language="yaml")

save_df()
save_state()
