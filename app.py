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
def extract_text(docx_file):
    doc = Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return "\n".join(full_text)

# Spacy Function
def is_action_item_spacy(line):
    doc = nlp(line)

    # Look for modal verbs or future tense (will, should, can, etc.)
    for token in doc:
        if token.tag_ in ("MD", "VBP", "VB") and token.dep_ == "ROOT":
            verb = token.lemma_.lower()
            if verb in ["send", "follow", "check", "remind", "schedule", "complete", "talk", "email", "review", "submit", "confirm"]:
                return True
    return False

# Rejex trigger patterns
ACTION_PATTERNS = [
    r"\b(can you|please|make sure|follow up|remind|send|complete|schedule|take care of|ensure|need to|have to|required to|I'll|I will|let's|should)\b.*",
]

# Regex for name detection (Lastname, Firstname format)
NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+,\s[A-Z][a-z]+(?:\s[A-Z]\.)?\b")

# Function to find action items in transcript
def find_action_items(text, keywords, default_owner, due_days):
    action_items = []
    lines = text.split('\n')
    due_date = (datetime.date.today() + datetime.timedelta(days=due_days)).isoformat()

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Match using keywords
        keyword_match = any(keyword.lower() in line_clean.lower() for keyword in keywords)

        # Match using regex patterns
        regex_match = any(re.search(pattern, line_clean, re.IGNORECASE) for pattern in ACTION_PATTERNS)

        # Match using spaCy NLP
        spacy_match = is_action_item_spacy(line_clean)

        if keyword_match or regex_match or spacy_match:
            # Try to extract names from the line
            name_match = NAME_PATTERN.search(line_clean)
            owner = name_match.group() if name_match else default_owner

            action_items.append({
                "Action Item": line_clean,
                "Owner": owner,
                "Due Date": due_date
            })

    if action_items:
        return pd.DataFrame(action_items)
    else:
        return pd.DataFrame(columns=["Action Item", "Owner", "Due Date"])

        
# Streamlit UI
st.set_page_config(page_title="Transcript Action Item Extractor", layout="centered")

st.title("Transcript Action Item Extractor")
st.write("Upload a Word document containing meeting transcripts to extract action items.")

# Upload file
uploaded_file = st.file_uploader("Choose a Word document", type=["docx"])

# Settings
default_owner = st.text_input("Default Owner", "Team Member")
due_days = st.number_input("Days until Due Date", min_value=0, max_value=30, value=7)
keywords = st.text_area("Keywords to search for (comma-separated)", "action, follow up, send, complete").split(",")

if uploaded_file:
    # Extract + Process
    text = extract_text(uploaded_file)
    df = find_action_items(text, keywords, default_owner, due_days)

if not df.empty:
    st.subheader("Action Items Found")
    st.dataframe(df)

    # Download as CSV
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv_data, "action_items.csv", "text/csv")

    # Download as JSON
    json_data = df.to_json(orient='records', indent=4)
    st.download_button("Download JSON", json_data, "action_items.json", "application/json")

    # Download as Markdown
    md_output = "\n".join([f"-**{row['Action Item']}** (Owner: {row['Owner']}, Due: {row['Due Date']})" for _, row in df.iterrows()])
    st.download_button("Download Markdown", md_output, "action_items.md", "text/markdown")

else:
    st.warning("No action items found with the given keywords. Please check the keywords or the content of the document.")

    

