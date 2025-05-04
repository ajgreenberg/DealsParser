import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI, RateLimitError
import requests
import json
import re
from typing import Dict

# --- API Setup ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
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

# --- GPT-4 (or 3.5) Extraction ---
def gpt_extract_summary(text: str) -> Dict:
    prompt = f"""
    You are an AI real estate analyst. Given the following offering memo text, extract key deal information and generate a short, neutral summary for a deal memo.

    Text:
    {text[:4000]}

    Respond ONLY with valid JSON. Do not include markdown or commentary.

    Fields:
    - Property Name
    - Location
    - Asset Class
    - Asking Price
    - Cap Rate
    - Square Footage or Unit Count
    - Key Highlights (bullet points)
    - Risks or Red Flags (bullet points)
    - Summary (neutral, 2–3 sentences)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw = response.choices[0].message.content
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()
        return json.loads(cleaned)

    except RateLimitError:
        st.error("⚠️ OpenAI rate limit reached. Please try again shortly.")
        return {}

    except json.JSONDecodeError as e:
        st.error("❌ GPT returned malformed JSON. See raw output below.")
        st.text_area("Raw GPT Output", raw, height=300)
        raise e

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

# --- Streamlit UI ---
st.title("📄 PDF Deal Memo Parser")

uploaded_file = st.file_uploader("Upload a Deal Memo PDF", type="pdf")

if uploaded_file:
    with st.spinner("Extracting text..."):
        text = extract_text_from_pdf(uploaded_file)
    
    with st.spinner("Analyzing with GPT..."):
        extracted_data = gpt_extract_summary(text)

    if extracted_data:
        st.subheader("🔍 Extracted Deal Information")
        for key, value in extracted_data.items():
            st.markdown(f"**{key}**: {value if not isinstance(value, list) else ', '.join(value)}")

        if st.button("📤 Save to Airtable"):
            save_to_airtable(extracted_data)
            st.success("✅ Saved to Airtable!")

        st.download_button("📥 Download JSON", data=json.dumps(extracted_data, indent=2), file_name="deal_summary.json")
