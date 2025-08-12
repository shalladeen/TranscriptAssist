import streamlit as st
import pandas as pd
from docx import Document
import io
import json
import datetime

# Function to extract text from a Word document
def extract_text(docx_file):
    doc = Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())
    return "\n".join(full_text)

# Function to find action items in transcript
def find_action_items(text, keywords, default_owner, due_days):
    action_items = []
    lines = text.split('\n')
    due_date = (datetime.date.today() + datetime.timedelta(days=due_days)).isoformat()

    for line in lines:
        if any(keyword.lower() in line.lower() for keyword in keywords):
            action_items.append({
                "Action Item": line.strip(),
                "Owner": default_owner,
                "Due Date": due_date
            })
            return pd.DataFrame(action_items)

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

    

