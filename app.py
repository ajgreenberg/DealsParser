import streamlit as st
import fitz  # PyMuPDF
from openai import OpenAI, RateLimitError
import requests
import json
import re
from bs4 import BeautifulSoup
import boto3
from typing import Dict
from datetime import datetime

# --- Secrets ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]

AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET = st.secrets["S3_BUCKET"]
S3_REGION = st.secrets["S3_REGION"]

# --- AWS S3 client ---
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)

def upload_to_s3(file_data, filename):
    try:
        key = f"deal-uploads/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"
        s3.upload_fileobj(file_data, S3_BUCKET, key, ExtraArgs={"ACL": "public-read"})
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"
    except Exception as e:
        st.warning(f"S3 Upload failed for {filename}: {e}")
        return None

def extract_text_from_pdf(uploaded_file) -> str:
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_url(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")

def gpt_extract_summary(text: str, source_desc: str = "a memo or webpage") -> Dict:
    prompt = f"""You are an AI real estate analyst. You are reviewing text from {source_desc}.

If key deal information is not clearly stated in the input, say so explicitly and do not guess. Do not make up property names, locations, or numbers.

Text:
{text[:4000]}

Return ONLY a valid JSON object with the following fields:
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
        st.error("⚠️ OpenAI rate limit reached. Please try again later.")
        return {}
    except json.JSONDecodeError as e:
        st.error("❌ GPT returned malformed JSON. See raw output below.")
        st.text_area("Raw GPT Output", raw, height=300)
        raise e

def save_to_airtable(data: Dict, raw_notes: str, attachment_urls: list) -> None:
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
        "Summary": data.get("Summary"),
        "Raw Notes": raw_notes,
        "Attachments": [{"url": u} for u in attachment_urls if u]
    }
    response = requests.post(url, headers=headers, json={"fields": fields})
    if response.status_code != 200:
        st.error(f"Airtable error: {response.text}")

# --- Streamlit UI ---
st.title("📄 Deal Parser with Attachments to S3")

source_type = st.radio("Input Type", ["Upload PDF", "Paste URL", "Paste Page Text"])
uploaded_pdf = None
source_text = ""
source_desc = ""

if source_type == "Upload PDF":
    uploaded_pdf = st.file_uploader("Upload Deal Memo PDF", type="pdf")
    if uploaded_pdf:
        with st.spinner("Extracting text from PDF..."):
            source_text = extract_text_from_pdf(uploaded_pdf)
            source_desc = "a PDF"
elif source_type == "Paste URL":
    url = st.text_input("Enter listing URL")
    if url:
        with st.spinner("Scraping text from URL..."):
            source_text = extract_text_from_url(url)
            source_desc = f"the webpage at {url}"
elif source_type == "Paste Page Text":
    pasted = st.text_area("Paste visible page content", height=300)
    if pasted:
        source_text = pasted
        source_desc = "pasted webpage content"

st.markdown("### 📋 Paste Any Extra Notes or Email Threads")
extra_notes = st.text_area("Additional deal context", height=200)

uploaded_files = st.file_uploader("📎 Upload Additional Attachments (PDF, XLSX, etc.)", accept_multiple_files=True)

if source_text:
    with st.spinner("Analyzing with GPT..."):
        summary = gpt_extract_summary(source_text, source_desc)

    if summary:
        st.subheader("🔍 Extracted Deal Information")
        for key, value in summary.items():
            st.markdown(f"**{key}**: {value if not isinstance(value, list) else ', '.join(value)}")

        if st.button("📤 Save to Airtable"):
            s3_urls = []

            # Upload main PDF to S3
            if uploaded_pdf:
                uploaded_pdf.seek(0)
                s3_urls.append(upload_to_s3(uploaded_pdf, uploaded_pdf.name))

            # Upload extra files
            for f in uploaded_files:
                f.seek(0)
                s3_urls.append(upload_to_s3(f, f.name))

            save_to_airtable(summary, raw_notes=extra_notes, attachment_urls=s3_urls)
            st.success("✅ Uploaded to Airtable with S3-hosted attachments!")

        st.download_button("📥 Download JSON", data=json.dumps(summary, indent=2), file_name="deal_summary.json")
