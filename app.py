import os
import pandas as pd
import streamlit as st
from st_keyup import st_keyup

VIDEO_DIR = st.sidebar.text_input("Video folder", "videos")

if not os.path.isdir(VIDEO_DIR):
    st.error(f"Folder '{VIDEO_DIR}' not found")
    st.stop()

CSV_PATH = os.path.join(VIDEO_DIR, "metadata.csv")
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    st.error(f"metadata.csv not found in {VIDEO_DIR}")
    st.stop()

# Determine label columns (int columns with only 0/1 values)
label_cols = [c for c in df.columns if pd.api.types.is_integer_dtype(df[c]) and df[c].dropna().isin([0, 1]).all()]

metadata_cols = [c for c in df.columns if c not in label_cols and c != "filename"]

if 'idx' not in st.session_state:
    st.session_state.idx = 0

sort_by = st.sidebar.selectbox("Sort videos by", df.columns.tolist(), index=df.columns.get_loc('filename'))

if sort_by:
    df = df.sort_values(by=sort_by).reset_index(drop=True)

video_files = df['filename'].tolist()

def save_df():
    df.to_csv(CSV_PATH, index=False)

# Navigation callbacks

def next_video():
    st.session_state.idx = (st.session_state.idx + 1) % len(df)

def prev_video():
    st.session_state.idx = (st.session_state.idx - 1) % len(df)

# Capture keyboard
key = st_keyup("", key="nav", label_visibility="collapsed")
if key == "ArrowRight":
    next_video()
elif key == "ArrowLeft":
    prev_video()
elif key.isdigit():
    n = int(key)
    if 1 <= n <= len(label_cols):
        col = label_cols[n-1]
        df.loc[st.session_state.idx, col] = 1 - df.loc[st.session_state.idx, col]
        st.session_state[f"lbl_{col}"] = bool(df.loc[st.session_state.idx, col])
        save_df()

current_file = video_files[st.session_state.idx]

st.write(f"### Video {st.session_state.idx + 1} of {len(video_files)} : {current_file}")
video_path = os.path.join(VIDEO_DIR, current_file)
if os.path.exists(video_path):
    video_bytes = open(video_path, 'rb').read()
    st.video(video_bytes)
else:
    st.warning(f"Video file '{current_file}' not found")

# Display metadata
st.subheader("Metadata")
st.table(df.loc[st.session_state.idx, metadata_cols].to_frame().T)

st.subheader("Labels (press 1..9 to toggle)")

for i, col in enumerate(label_cols):
    default = bool(df.loc[st.session_state.idx, col])
    checked = st.checkbox(f"{i+1}. {col}", value=default, key=f"lbl_{col}")
    if checked != default:
        df.loc[st.session_state.idx, col] = int(checked)
        save_df()

new_label = st.text_input("Add new label")
if st.button("Add Label") and new_label:
    if new_label not in df.columns:
        df[new_label] = 0
        label_cols.append(new_label)
        df.loc[st.session_state.idx, new_label] = 1
        st.session_state[f"lbl_{new_label}"] = True
        save_df()
        st.experimental_rerun()

col1, col2 = st.columns(2)
with col1:
    st.button("◀ Previous", on_click=prev_video, key="prev")
with col2:
    st.button("Next ▶", on_click=next_video, key="next")

save_df()
