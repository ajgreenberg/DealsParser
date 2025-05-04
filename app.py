import streamlit as st
import fitz
import docx
import textract
from openai import OpenAI
import requests
import json
import re
import boto3
from typing import Dict
from datetime import datetime

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET = st.secrets["S3_BUCKET"]
S3_REGION = st.secrets["S3_REGION"]

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)

def upload_to_s3(file_data, filename):
    key = f"deal-uploads/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"
    s3.upload_fileobj(file_data, S3_BUCKET, key)
    return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"

def extract_text_from_pdf(file) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(file) -> str:
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_doc(file) -> str:
    return textract.process(file.name).decode("utf-8")

def summarize_notes(notes: str) -> str:
    if not notes.strip():
        return ""
    prompt = f"Summarize the following deal notes or email thread in 2-4 concise, neutral bullet points:\n\n{notes}"
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content.strip()

def extract_contact_info(text: str) -> str:
    prompt = f"From the following deal memo or email text, extract any contact info for brokers or sponsors. If none is found, say 'None'.\n\n{text[:3000]}"
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content.strip()

def gpt_extract_summary(text: str, deal_type: str) -> Dict:
    prompt = f"""You are an AI real estate analyst reviewing a {deal_type.lower()} opportunity.

Text:
{text[:4000]}

Return JSON with:
- Property Name
- Location
- Asset Class
- Purchase Price
- Loan Amount
- In-Place Cap Rate
- Stabilized Cap Rate
- Interest Rate
- Term
- DSCR
- Exit Strategy
- Projected IRR
- Hold Period
- Square Footage or Unit Count
- Key Highlights (bullet points)
- Risks or Red Flags (bullet points)
- Summary (2-3 sentences)
"""
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    raw = res.choices[0].message.content
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    return json.loads(cleaned)

def create_airtable_record(data: Dict, notes: str, attachments: list, deal_type: str, contact_info: str):
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    fields = {
        "Deal Type": [deal_type],
        "Summary": data.get("Summary"),
        "Raw Notes": notes,
        "Contact Info": contact_info,
        "Attachments": [{"url": u} for u in attachments if u],
        "Key Highlights": "\n".join(data.get("Key Highlights", [])),
        "Risks": "\n".join(data.get("Risks or Red Flags", [])),
        "Property Name": data.get("Property Name"),
        "Location": data.get("Location"),
        "Asset Class": data.get("Asset Class"),
        "Purchase Price": data.get("Purchase Price"),
        "Loan Amount": data.get("Loan Amount"),
        "In-Place Cap Rate": data.get("In-Place Cap Rate"),
        "Stabilized Cap Rate": data.get("Stabilized Cap Rate"),
        "Interest Rate": data.get("Interest Rate"),
        "Term": data.get("Term"),
        "DSCR": data.get("DSCR"),
        "Exit Strategy": data.get("Exit Strategy"),
        "Projected IRR": data.get("Projected IRR"),
        "Hold Period": data.get("Hold Period"),
        "Size": data.get("Square Footage or Unit Count")
    }

    payload = {"fields": fields}
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code not in [200, 201]:
        st.error(f"Airtable error: {res.text}")
    else:
        st.success("✅ Deal saved to Airtable!")

# --- Streamlit UI ---
st.title("📄 Deal Parser")

deal_type = st.radio("💼 Select Deal Type", ["🏦 Debt", "🏢 Equity"], horizontal=True)
deal_type_value = "Debt" if "Debt" in deal_type else "Equity"

uploaded_main = st.file_uploader("📄 Upload Deal Memo (optional)", type=["pdf", "doc", "docx"])
extra_notes = st.text_area("🗒 Paste deal notes or email thread", height=200)
uploaded_files = st.file_uploader("📎 Upload supporting files (optional)", type=["pdf", "doc", "docx", "xls", "xlsx", "jpg", "png"], accept_multiple_files=True)

if st.button("🚀 Run Deal Parser"):
    source_text = ""

    if uploaded_main:
        ext = uploaded_main.name.lower().split(".")[-1]
        if ext == "pdf":
            source_text = extract_text_from_pdf(uploaded_main)
        elif ext == "docx":
            source_text = extract_text_from_docx(uploaded_main)
        elif ext == "doc":
            uploaded_main.seek(0)
            source_text = extract_text_from_doc(uploaded_main)

    if not source_text and not extra_notes.strip():
        st.warning("Please upload a memo or enter some notes.")
    else:
        combined_text = (source_text + "\n\n" + extra_notes).strip()
        with st.spinner("Analyzing deal..."):
            summary = gpt_extract_summary(combined_text, deal_type_value)
            summarized_notes = summarize_notes(extra_notes)
            contact_info = extract_contact_info(combined_text)

        st.subheader("🔍 Deal Summary")
        for k, v in summary.items():
            st.markdown(f"**{k}**: {v if not isinstance(v, list) else ', '.join(v)}")

        st.markdown("**Contact Info:**")
        st.text(contact_info)

        s3_urls = []
        if uploaded_main:
            uploaded_main.seek(0)
            s3_urls.append(upload_to_s3(uploaded_main, uploaded_main.name))
        for f in uploaded_files:
            f.seek(0)
            s3_urls.append(upload_to_s3(f, f.name))

        if st.checkbox("📤 Upload this deal to Airtable?"):
            with st.spinner("Uploading to Airtable..."):
                create_airtable_record(summary, summarized_notes, s3_urls, deal_type_value, contact_info)
