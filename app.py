import streamlit as st
import fitz  # PyMuPDF
import openai
import requests
import json
from typing import Dict

# --- API Keys from Streamlit secrets ---
openai.api_key = st.secrets["OPENAI_API_KEY"]
AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]

# --- PDF Parsing ---
def extract_text_from_pdf(uploaded_file) -> str:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# --- GPT-4 Extraction ---
def gpt_extract_summary(text: str) -> Dict:
    prompt = f"""
    You are an AI real estate analyst. Given the following offering memo text, extract key deal information and generate a short, neutral summary for a deal memo.

    Text:
    {text[:4000]}  # limit to avoid token overload

    Return as JSON with the following fields:
    - Property Name
    - Location
    - Asset Class
    - Asking Price
    - Cap Rate
    - Square Footage or Unit Count
    - Key Highlights (bullet points)
    - Risks or Red Flags (bullet points)
    - Summary (neutral, 2-3 sentences)

    JSON:
    """
    from openai import OpenAI

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return json.loads(response.choices[0].message.content)

# --- Save to Airtable ---
def save_to_airtable(data: Dict) -> None:
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    fields = {
        "Property Name": data.get("Property Name"),
        "Location": data.get("Location"),
        "Asset Class": data.get("Asset Class"),
        "Asking Price": data.get("Asking Price"),
        "Cap Rate": data.get("Cap Rate"),
        "Size": data.get("Square Footage or Unit Count"),
        "Key Highlights": "\n".join(data.get("Key Highlights", [])),
        "Risks": "\n".join(data.get("Risks or Red Flags", [])),
        "Summary": data.get("Summary")
    }
    response = requests.post(url, headers=headers, json={"fields": fields})
    if response.status_code != 200:
        st.error(f"Airtable error: {response.text}")

# --- Streamlit App ---
st.title("📄 PDF Deal Memo Parser")

uploaded_file = st.file_uploader("Upload a Deal Memo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Extracting text..."):
        text = extract_text_from_pdf(uploaded_file)
    
    with st.spinner("Analyzing with GPT-4..."):
        extracted_data = gpt_extract_summary(text)

    st.subheader("🔍 Extracted Deal Information")
    for key, value in extracted_data.items():
        st.markdown(f"**{key}**: {value if not isinstance(value, list) else ', '.join(value)}")

    if st.button("📤 Save to Airtable"):
        save_to_airtable(extracted_data)
        st.success("✅ Saved to Airtable!")

    st.download_button("📥 Download JSON", data=json.dumps(extracted_data, indent=2), file_name="deal_summary.json")
