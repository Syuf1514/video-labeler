import json
import logging
import os
import sys
import tempfile

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yaml

# -----------------------------------------------------
# 1) set_page_config must be the very first Streamlit call
# -----------------------------------------------------
st.set_page_config(layout="centered")

# -----------------------------------------------------
# 2) Inject CSS
# -----------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.5rem;
        max-width: 80% !important;
        width: 80% !important;
    }
    video {
        width: 100%;
        max-height: 80vh !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------
# 3) Keyboard listener at the top so it always captures keys
# -----------------------------------------------------
if "last_key" not in st.session_state:
    st.session_state.last_key = None

key = components.html(
    """
    <script>
        window.addEventListener('keydown', (e) => {
            Streamlit.setComponentValue(e.key);
            e.preventDefault();
        });
    </script>
    """,
    height=0,
)

LOG_PATH = "app.log"
STATE_PATH = "state.json"

# -----------------------------------------------------
# 4) Logging setup
# -----------------------------------------------------
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def log_exception(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))


sys.excepthook = log_exception


# -----------------------------------------------------
# 5) State helpers: load_state / save_state / save_df
# -----------------------------------------------------
def load_state():
    data = {"idx": 0, "csv_path": "", "sort_by": "path", "order": "Ascending"}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH) as f:
                stored = json.load(f)
            data.update(stored)
        except Exception as e:
            logging.error("Failed to load state: %s", e)
    return data


def save_state():
    st.session_state.is_saving = True
    with st.spinner("Saving state…"):
        to_write = {
            "idx": st.session_state.idx,
            "csv_path": st.session_state.csv_path,
            "sort_by": st.session_state.get("sort_by", "path"),
            "order": st.session_state.get("order", "Ascending"),
        }
        try:
            tmp_f, tmp_path = tempfile.mkstemp(prefix="state_", suffix=".json")
            with os.fdopen(tmp_f, "w") as f:
                json.dump(to_write, f)
            os.replace(tmp_path, STATE_PATH)
        except Exception as e:
            logging.error("Failed to save state: %s", e)
    st.session_state.is_saving = False


def save_df(df, csv_path):
    st.session_state.is_saving = True
    with st.spinner("Saving metadata…"):
        try:
            tmp_f, tmp_path = tempfile.mkstemp(prefix="metadata_", suffix=".csv")
            df.to_csv(tmp_path, index=False)
            os.replace(tmp_path, csv_path)
        except Exception as e:
            logging.error("Failed to save CSV: %s", e)
    st.session_state.is_saving = False


# -----------------------------------------------------
# 6) Initialize session_state defaults if missing
# -----------------------------------------------------
if any(k not in st.session_state for k in ("idx", "csv_path", "sort_by", "order", "is_saving")):
    saved = load_state()
    st.session_state.idx = saved.get("idx", 0)
    st.session_state.csv_path = saved.get("csv_path", "")
    st.session_state.sort_by = saved.get("sort_by", "path")
    st.session_state.order = saved.get("order", "Ascending")
    st.session_state.is_saving = False

# We also track “last_sort” so we can reset idx whenever the user flips sort criteria
if "last_sort" not in st.session_state:
    st.session_state.last_sort = (st.session_state.sort_by, st.session_state.order)

# -----------------------------------------------------
# 7) Sidebar: CSV path input
# -----------------------------------------------------
st.sidebar.title("Configuration")

CSV_PATH_INPUT = st.sidebar.text_input(
    "Metadata CSV file",
    value=st.session_state.csv_path,
    key="csv_path_input",
    help="Path to your metadata CSV (must include a 'path' column pointing to each video file)"
)

# If the user actually typed a different CSV path than the one stored in session_state, update and reset idx.
if CSV_PATH_INPUT != st.session_state.csv_path:
    st.session_state.csv_path = CSV_PATH_INPUT
    st.session_state.idx = 0
    save_state()
    st.experimental_rerun()

CSV_PATH = st.session_state.csv_path

if not os.path.isfile(CSV_PATH):
    st.error(f"File '{CSV_PATH}' not found")
    logging.error("File '%s' not found", CSV_PATH)
    st.stop()

# -----------------------------------------------------
# 8) Load CSV into DataFrame
# -----------------------------------------------------
try:
    df = pd.read_csv(CSV_PATH)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    logging.error("Failed to read CSV '%s': %s", CSV_PATH, e)
    st.stop()

if "path" not in df.columns:
    st.error("CSV must contain a 'path' column with video file paths")
    logging.error("CSV '%s' missing 'path' column", CSV_PATH)
    st.stop()

# -----------------------------------------------------
# 9) “Remove Label” and “Add Label” UI (run before computing label_cols)
# -----------------------------------------------------
label_cols_before = []
for c in df.columns:
    if c == "path":
        continue
    if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c]):
        nonnull_vals = df[c].dropna().unique().tolist()
        if all(val in (0, 1) for val in nonnull_vals):
            label_cols_before.append(c)

st.sidebar.markdown("---")
st.sidebar.subheader("Remove Labels")
labels_to_remove = st.sidebar.multiselect(
    "Select labels to delete:",
    options=label_cols_before
)
if st.sidebar.button("Remove Selected Labels"):
    if labels_to_remove:
        for lbl in labels_to_remove:
            if lbl in df.columns:
                df.drop(columns=[lbl], inplace=True)
            for k in list(st.session_state.keys()):
                if k.startswith(f"lbl_{lbl}_"):
                    del st.session_state[k]
        save_df(df, CSV_PATH)
        logging.info("Removed labels: %s", labels_to_remove)
        st.sidebar.success(f"Removed: {', '.join(labels_to_remove)}")
        st.experimental_rerun()
    else:
        st.sidebar.warning("No labels selected.")

# 9b) Add New Label UI
st.sidebar.markdown("---")
new_label = st.sidebar.text_input("Add New Label")
if st.sidebar.button("Add Label"):
    if new_label:
        if new_label in df.columns:
            st.sidebar.warning(f"'{new_label}' already exists.")
        else:
            df[new_label] = 0
            save_df(df, CSV_PATH)
            logging.info("Added new label: %s", new_label)
            st.sidebar.success(f"Added '{new_label}'")
            st.experimental_rerun()
    else:
        st.sidebar.warning("Please enter a label name.")

# -----------------------------------------------------
# 10) Compute label_cols AFTER add/remove
# -----------------------------------------------------
label_cols = []
for c in df.columns:
    if c == "path":
        continue
    if pd.api.types.is_integer_dtype(df[c]) or pd.api.types.is_float_dtype(df[c]):
        nonnull_vals = df[c].dropna().unique().tolist()
        if all(val in (0, 1) for val in nonnull_vals):
            label_cols.append(c)

# -----------------------------------------------------
# 11) Compute metadata_cols
# -----------------------------------------------------
metadata_cols = [c for c in df.columns if c not in label_cols and c != "path"]

# -----------------------------------------------------
# 12) sort_by & order widgets (preserve previous choice)
# -----------------------------------------------------
if ("sort_by" not in st.session_state) or (st.session_state.sort_by not in df.columns):
    st.session_state.sort_by = "path"

sort_by = st.sidebar.selectbox(
    "Sort videos by",
    df.columns.tolist(),
    index=df.columns.tolist().index(st.session_state.sort_by),
    key="sort_by"
)

if ("order" not in st.session_state) or (st.session_state.order not in ["Ascending", "Descending"]):
    st.session_state.order = "Ascending"

order = st.sidebar.radio(
    "Order",
    ["Ascending", "Descending"],
    index=0 if st.session_state.order == "Ascending" else 1,
    key="order",
    horizontal=True
)

with st.sidebar.expander("Logs (last 20 lines)"):
    if os.path.exists(LOG_PATH):
        try:
            with open(LOG_PATH) as f:
                lines = f.readlines()
            st.text("".join(lines[-20:]))
        except Exception as e:
            st.text(f"Failed to read log: {e}")

# -----------------------------------------------------
# 13) Detect changes in sort settings, reset idx if needed
# -----------------------------------------------------
current_sort = (st.session_state.sort_by, st.session_state.order)
if current_sort != st.session_state.last_sort:
    st.session_state.idx = 0
    st.session_state.last_sort = current_sort
    save_state()

# -----------------------------------------------------
# 14) Sort the DataFrame
# -----------------------------------------------------
if sort_by:
    asc = (order == "Ascending")
    df = df.sort_values(
        by=[sort_by, "path"],
        ascending=[asc, True]
    ).reset_index(drop=True)

video_files = df["path"].tolist()
n_videos = len(video_files)
if n_videos == 0:
    st.error("No videos listed in CSV.")
    st.stop()


# -----------------------------------------------------
# 15) Navigation callbacks
# -----------------------------------------------------
def _update_idx(new_idx):
    st.session_state.idx = new_idx % n_videos
    save_state()
    logging.info("Moved to video #%d: %s", st.session_state.idx, video_files[st.session_state.idx])


def next_video():
    if not st.session_state.is_saving:
        _update_idx(st.session_state.idx + 1)


def prev_video():
    if not st.session_state.is_saving:
        _update_idx(st.session_state.idx - 1)


# -----------------------------------------------------
# 16) Keyboard handling
# -----------------------------------------------------
current_idx = st.session_state.idx

if not st.session_state.is_saving:
    if isinstance(key, str) and (key != st.session_state.last_key):
        if key in ("ArrowRight", " "):
            next_video()
            logging.info("Next via keyboard")
        elif key == "ArrowLeft":
            prev_video()
            logging.info("Previous via keyboard")
        elif key.isdigit():
            num = int(key)
            if 1 <= num <= len(label_cols):
                col = label_cols[num - 1]
                idx = st.session_state.idx
                df.loc[idx, col] = 1 - df.loc[idx, col]
                save_df(df, CSV_PATH)
                logging.info("Toggled label %s via keyboard", col)
        st.session_state.last_key = key
    elif key is None:
        st.session_state.last_key = None

# -----------------------------------------------------
# 17) Main interface
# -----------------------------------------------------
current_idx = st.session_state.idx
st.markdown(
    f"<div style='text-align:right;color:gray'>{current_idx + 1}/{n_videos}</div>",
    unsafe_allow_html=True,
)
current_file = video_files[current_idx]
video_path = current_file

ctrl_col, video_col, meta_col = st.columns([1, 3, 2])

# --- Video Column ---
with video_col:
    container = st.empty()
    if os.path.exists(video_path):
        container.video(video_path, start_time=0)
    else:
        container.warning(f"Video file not found: {video_path}")
        logging.error("Video file not found: %s", video_path)

# --- Controls Column (labels + navigation) ---
with ctrl_col:
    st.caption(os.path.basename(current_file))


    def toggle_label(col):
        idx = st.session_state.idx
        val = st.session_state[f"lbl_{col}_{idx}"]
        df.loc[idx, col] = int(val)
        save_df(df, CSV_PATH)
        logging.info("Toggled label %s via checkbox", col)


    for i, col in enumerate(label_cols):
        key_name = f"lbl_{col}_{current_idx}"
        if key_name in st.session_state:
            del st.session_state[key_name]
        initial_val = bool(df.loc[current_idx, col])
        st.checkbox(
            f"{i + 1}. {col}",
            value=initial_val,
            key=key_name,
            on_change=toggle_label,
            args=(col,),
            help="Click or press the corresponding number key to toggle."
        )

    nav1, nav2 = st.columns([1, 1])
    with nav1:
        st.button(
            "◀ Previous",
            on_click=prev_video,
            key="prev_btn",
            disabled=st.session_state.is_saving
        )
    with nav2:
        st.button(
            "Next ▶",
            on_click=next_video,
            key="next_btn",
            disabled=st.session_state.is_saving
        )

# --- Metadata Column ---
with meta_col:
    st.caption("Metadata")
    metadata = df.loc[current_idx, metadata_cols].to_dict()
    yaml_text = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    st.code(yaml_text, language="yaml")
