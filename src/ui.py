import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from .constants import DEFAULT_KEYWORDS

st.set_page_config(
    page_title="Action Item Extractor",
    layout="wide",
)

def load_css(path: str = "style.css") -> None:
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
    except FileNotFoundError:
        st.info(f"Note: '{path}' not found. Skipping custom CSS.")
        return
    
    if hasattr(st, "html"):
        st.html(f"<style>{css}</style>")
    else:
        st.info(
            "Running on a Streamlit build without 'st.html'. "
            "Global CSS not applied (theme from config.toml still works)."
        )

load_css()
        
def show_header():
    st.title("Extract Action Items From Your Transcript")
    st.caption(
        "Upload a .docx meeting transcript and extract actionable tasks with "
        "speaker attribution. Export results in CSV, JSON, or Markdown."
    )


def show_upload():
    st.subheader("Upload Your File")
    return st.file_uploader("Choose a Word document (.docx)", type=["docx"])


def show_tuning():
    st.subheader("Refine Detection")
    raw = st.text_area("Comma-separated keywords", DEFAULT_KEYWORDS)
    return raw.split(",") if raw else []


def show_results(df: pd.DataFrame):
    st.success(f"Found {len(df)} action item(s).")
    st.subheader("Extracted Action Items")
    st.dataframe(df, height=300, use_container_width=True)


def show_export(df: pd.DataFrame):
    st.subheader("Export Results")
    col1, col2, col3 = st.columns(3)

    with col1:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV", csv_data, "action_items.csv", "text/csv"
        )

    with col2:
        json_data = df.to_json(orient="records", indent=4)
        st.download_button(
            "Download JSON", json_data, "action_items.json", "application/json"
        )

    with col3:
        md_output = "\n".join(
            [f"- **{row['Action Item']}** _(Type: {row['Type']})_" for _, row in df.iterrows()]
        )
        st.download_button(
            "Download Markdown", md_output, "action_items.md", "text/markdown"
        )
