from pathlib import Path
import streamlit as st
import pandas as pd

from src.extract import extract_speaker_blocks, extract_names
from src.detect import find_action_items_with_speakers
from src.ui import show_header, show_upload, show_tuning, show_results, show_export

st.set_page_config(page_title="Transcript Action Item Extractor", layout="wide")

show_header()

uploaded_file = show_upload()
keywords = show_tuning()

if uploaded_file:
    with st.spinner("Analyzing transcript…"):
        speaker_blocks = extract_speaker_blocks(uploaded_file)
        _, first_names = extract_names(uploaded_file)
        df = find_action_items_with_speakers(speaker_blocks, keywords)

    if not df.empty:
        show_results(df)
        show_export(df)
    else:
        st.info("No action items detected in the transcript.")