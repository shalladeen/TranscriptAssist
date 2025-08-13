import streamlit as st
import pandas as pd
from docx import Document
import spacy
import re
import io
import json
import datetime

nlp = spacy.load("en_core_web_sm")
df = pd.DataFrame()




# Function to extract text from a Word document
def extract_speaker_blocks(docx_file):
    doc = Document(docx_file)
    speaker_pattern = re.compile(r"^([A-Z][a-z]+,\s[A-Z][a-z]+(?:\s[A-Z]\.)?)\s+(\d{1,2}:\d{2}(?::\d{2})?)")

    
    blocks = []
    current_speaker = None

    for para in doc.paragraphs:
        line = para.text.strip()
        if not line:
            continue

        match = speaker_pattern.match(line)
        if match:
            current_speaker = match.group(1)
        elif current_speaker:
            blocks.append((current_speaker, line))

    return blocks


# Spacy Function
def is_action_item_spacy(line):
    doc = nlp(line)

    # Look for modal verbs or future tense (will, should, can, etc.)
    for token in doc:
        if token.tag_ in ("MD", "VBP", "VB") and token.dep_ == "ROOT":
            verb = token.lemma_.lower()
            if verb in ["share", "talk", "assign", "send", "remind", "follow", "check", "email", "connect", "complete", "submit", "update"]:
                return True
    return False

# Rejex trigger patterns
ACTION_PATTERNS = [
    r"\b(can you|please|make sure|follow up|remind|send|complete|schedule|take care of|ensure|need to|have to|required to|I'll|I will|let's|should)\b.*",
]

# Regex for name detection (Lastname, Firstname format)
NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+,\s[A-Z][a-z]+(?:\s[A-Z]\.)?\b")

# Function to find action items in transcript
def find_action_items_with_speakers(speaker_blocks, keywords, due_days):
    action_items = []
    due_date = (datetime.date.today() + datetime.timedelta(days=due_days)).isoformat()

    for speaker, line in speaker_blocks:
        line_clean = line.strip()
        if not line_clean:
            continue

        keyword_match = any(keyword.lower() in line_clean.lower() for keyword in keywords)
        regex_match = any(re.search(pattern, line_clean, re.IGNORECASE) for pattern in ACTION_PATTERNS)
        spacy_match = is_action_item_spacy(line_clean)

        if keyword_match or regex_match or spacy_match:
            action_items.append({
                "Action Item": line_clean,
                "Owner": speaker,
                "Due Date": due_date
            })

    return pd.DataFrame(action_items) if action_items else pd.DataFrame(columns=["Action Item", "Owner", "Due Date"])


        
# Streamlit UI
st.set_page_config(page_title="Transcript Action Item Extractor", layout="wide")

st.title("Transcript Action Item Extractor")
st.write(
    "Upload a `.docx` meeting transcript to extract action items with owner attribution."
)

# Upload
uploaded_file = st.file_uploader("Upload Word document", type=["docx"])

# Always-visible settings
st.markdown("### Settings")
default_owner = st.text_input("Default owner (if no name is detected)", "Team Member")
due_days = st.number_input("Days until due date", min_value=0, max_value=30, value=7)
keywords = st.text_area(
    "Comma-separated keywords to help detect action items",
    "action, follow up, send, complete, email, share, remind, assign, connect, confirm"
).split(",")

# Processing and output
if uploaded_file:
    with st.spinner("Processing transcript..."):
        speaker_blocks = extract_speaker_blocks(uploaded_file)
        df = find_action_items_with_speakers(speaker_blocks, keywords, due_days)


    if not df.empty:
        st.success(f"Found {len(df)} action item(s).")

        st.markdown("### Extracted Action Items")
        st.dataframe(df, height=500, use_container_width=True)

        st.markdown("### Download Results")
        col1, col2, col3 = st.columns(3)

        with col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv_data, "action_items.csv", "text/csv")

        with col2:
            json_data = df.to_json(orient='records', indent=4)
            st.download_button("Download JSON", json_data, "action_items.json", "application/json")

        with col3:
            md_output = "\n".join([
                f"- **{row['Action Item']}** (Owner: {row['Owner']}, Due: {row['Due Date']})"
                for _, row in df.iterrows()
            ])
            st.download_button("Download Markdown", md_output, "action_items.md", "text/markdown")
    else:
        st.warning("No action items found. Try adjusting keywords or checking the formatting.")
