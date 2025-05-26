import streamlit as st
import fitz
import docx
import textract
from openai import OpenAI
import requests
import json
import re
import boto3
from typing import Dict, List
from datetime import datetime

# --- Custom CSS for Apple-like styling ---
st.set_page_config(
    page_title="DealFlow AI",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
    <style>
        /* Main container */
        .main {
            padding: 1rem;
        }
        
        /* Typography */
        h1 {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 700 !important;
            font-size: 2.2rem !important;
            margin-bottom: 1rem !important;
            color: #1D1D1F !important;
        }
        
        h2 {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 600 !important;
            font-size: 1.3rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
            color: #1D1D1F !important;
        }
        
        /* Form styling */
        .stRadio > label {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 500;
            color: #1D1D1F;
            margin-bottom: 0.5rem;
        }
        
        /* Input field styling */
        .stTextInput > label {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 500;
            color: #1D1D1F;
            margin-bottom: 0.25rem;
        }
        
        .stTextInput > div > div {
            border: 1px solid #E6E6E6 !important;
            border-radius: 6px !important;
            background-color: #FFFFFF !important;
        }
        
        /* Editable field styling */
        .stTextInput > div > div:hover {
            border-color: #0c3c60 !important;
            box-shadow: 0 0 0 1px #0c3c60 !important;
        }
        
        .stTextInput > div > div:focus-within {
            border-color: #0c3c60 !important;
            box-shadow: 0 0 0 2px #0c3c60 !important;
        }
        
        /* Button styling */
        .stButton > button {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0c3c60 !important;
            color: white !important;
            border-radius: 6px !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 500 !important;
            border: none !important;
            transition: all 0.2s ease !important;
            width: auto !important;
            margin: 0.5rem 0 !important;
        }
        
        .stButton > button:hover {
            background-color: #0d4470 !important;
            transform: scale(1.02);
        }
        
        /* File uploader styling */
        .uploadedFile {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            border: 1px solid #E6E6E6;
            border-radius: 6px;
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        /* Success message styling */
        .success {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 0.75rem;
            border-radius: 6px;
            background-color: #F5F5F7;
            margin: 0.5rem 0;
        }
        
        /* Divider styling */
        hr {
            margin: 1rem 0 !important;
            border: none;
            border-top: 1px solid #E6E6E6;
        }
        
        /* Form container */
        .stForm {
            background-color: #F5F5F7;
            padding: 1.5rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        
        /* Text area styling */
        .stTextArea > label {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 500;
            color: #1D1D1F;
            margin-bottom: 0.25rem;
        }
        
        .stTextArea > div > div {
            border-radius: 6px !important;
            border: 1px solid #E6E6E6 !important;
            background-color: #FFFFFF !important;
        }
        
        .stTextArea > div > div:hover {
            border-color: #0c3c60 !important;
            box-shadow: 0 0 0 1px #0c3c60 !important;
        }
        
        .stTextArea > div > div:focus-within {
            border-color: #0c3c60 !important;
            box-shadow: 0 0 0 2px #0c3c60 !important;
        }
        
        /* Editable form section */
        .editable-form {
            background-color: #F8F8FA;
            border: 1px solid #E6E6E6;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* Compact spacing for form fields */
        .stForm > div > div > div {
            margin-bottom: 0.5rem !important;
        }
        
        /* Help text styling */
        .stTextInput > div > div > .help {
            color: #6B7280 !important;
            font-size: 0.875rem !important;
            margin-top: 0.25rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Config and Clients ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
AIRTABLE_PAT         = st.secrets["AIRTABLE_PAT"]
AIRTABLE_BASE_ID     = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME  = st.secrets["AIRTABLE_TABLE_NAME"]
AWS_ACCESS_KEY_ID    = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY= st.secrets["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET            = st.secrets["S3_BUCKET"]
S3_REGION            = st.secrets["S3_REGION"]

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)

# --- Helper Functions ---
def upload_to_s3(file_data, filename) -> str:
    key = f"deal-uploads/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{filename}"
    s3.upload_fileobj(file_data, S3_BUCKET, key)
    return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"

def extract_text_from_pdf(f) -> str:
    doc = fitz.open(stream=f.read(), filetype="pdf")
    return "\n".join(page.get_text() for page in doc)

def extract_text_from_docx(f) -> str:
    doc = docx.Document(f)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_text_from_doc(f) -> str:
    return textract.process(f.name).decode("utf-8")

def summarize_notes(notes: str) -> str:
    if not notes.strip():
        return ""
    prompt = (
        "Summarize the following deal notes or email thread in 2-4 concise, neutral bullet points:\n\n"
        f"{notes}"
    )
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content.strip()

def extract_contact_info(text: str) -> str:
    prompt = (
        "Extract the contact information (name, company, phone, and email) of any brokers, "
        "sponsors, or agents from the following text. Be thorough and include details even if they "
        "are buried in an email signature or footnote. Return in plain text format.\n\nText:\n"
        + text[:3500]
    )
    res = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content.strip()

def gpt_extract_summary(text: str, deal_type: str) -> Dict:
    prompt = (
        f"You are an AI real estate analyst reviewing a {deal_type.lower()} opportunity.\n\n"
        f"Text:\n{text[:4000]}\n\n"
        "Return JSON with:\n"
        "- Property Name\n"
        "- Location\n"
        "- Asset Class\n"
        "- Sponsor\n"
        "- Broker\n"
        "- Purchase Price\n"
        "- Loan Amount\n"
        "- In-Place Cap Rate\n"
        "- Stabilized Cap Rate\n"
        "- Interest Rate\n"
        "- Term\n"
        "- Exit Strategy\n"
        "- Projected IRR\n"
        "- Hold Period\n"
        "- Square Footage or Unit Count\n"
        "- Key Highlights (bullet points)\n"
        "- Risks or Red Flags (bullet points)\n"
        "- Summary (2-3 sentences)\n"
    )
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    raw = res.choices[0].message.content
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    cleaned = re.sub(r"^[^\{]*", "", cleaned, flags=re.DOTALL)
    return json.loads(cleaned)

def generate_maps_link(address: str) -> str:
    """Generate a Google Maps link from an address."""
    if not address:
        return ""
    formatted_address = address.replace(' ', '+')
    return f"https://www.google.com/maps/search/?api=1&query={formatted_address}"

def create_airtable_record(
    data: Dict,
    raw_notes: str,
    attachments: List[str],
    deal_type: str,
    contact_info: str
):
    # Always tag new deals as "Pursuing"
    status = "Pursuing"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    
    # Generate maps link from location
    maps_link = generate_maps_link(data.get("Location", ""))
    
    fields = {
        "Deal Type": [deal_type],
        "Status": status,
        "Summary": data.get("Summary"),
        "Raw Notes": raw_notes,
        "Contact Info": contact_info,
        "Sponsor": data.get("Sponsor"),
        "Broker": data.get("Broker"),
        "Attachments": [{"url": u} for u in attachments],
        "Key Highlights": "\n".join(data.get("Key Highlights", [])),
        "Risks": "\n".join(data.get("Risks or Red Flags", [])),
        "Property Name": data.get("Property Name"),
        "Location": data.get("Location"),
        "Maps Link": maps_link,
        "Asset Class": data.get("Asset Class"),
        "Purchase Price": data.get("Purchase Price"),
        "Loan Amount": data.get("Loan Amount"),
        "In-Place Cap Rate": data.get("In-Place Cap Rate"),
        "Stabilized Cap Rate": data.get("Stabilized Cap Rate"),
        "Interest Rate": data.get("Interest Rate"),
        "Term": data.get("Term"),
        "Exit Strategy": data.get("Exit Strategy"),
        "Projected IRR": data.get("Projected IRR"),
        "Hold Period": data.get("Hold Period"),
        "Size": data.get("Square Footage or Unit Count"),
    }
    resp = requests.post(
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}",
        headers=headers,
        json={"fields": fields}
    )
    if resp.status_code not in (200, 201):
        st.error(f"Airtable error: {resp.text}")

# --- Streamlit UI ---
st.markdown("<h1>DealFlow AI</h1>", unsafe_allow_html=True)

st.markdown("<h2>Deal Information</h2>", unsafe_allow_html=True)
deal_type = st.radio("Select Deal Type", ["🏢 Equity", "🏦 Debt"], horizontal=True)
deal_type_value = "Debt" if "Debt" in deal_type else "Equity"

uploaded_main = st.file_uploader("Upload Deal Memo", type=["pdf","doc","docx"], 
    help="Upload the main deal memo document")

uploaded_files = st.file_uploader(
    "Supporting Documents",
    type=["pdf","doc","docx","xls","xlsx","jpg","png"],
    accept_multiple_files=True,
    help="Upload any additional supporting documents"
)

extra_notes = st.text_area(
    "Deal Notes or Email Thread",
    height=150,
    help="Paste any additional notes or email correspondence"
)

analyze_button = st.button("🚀 Analyze Deal")

if analyze_button:
    with st.spinner("🔍 Parsing deal…"):
        source_text = ""
        if uploaded_main:
            ext = uploaded_main.name.lower().rsplit(".",1)[-1]
            if ext == "pdf":
                source_text = extract_text_from_pdf(uploaded_main)
            elif ext == "docx":
                source_text = extract_text_from_docx(uploaded_main)
            else:
                uploaded_main.seek(0)
                source_text = extract_text_from_doc(uploaded_main)

        if not source_text and not extra_notes.strip():
            st.warning("Please upload a memo or enter some notes.")
        else:
            combined = (source_text + "\n\n" + extra_notes).strip()
            summary       = gpt_extract_summary(combined, deal_type_value)
            notes_summary = summarize_notes(extra_notes)
            contact_info  = extract_contact_info(combined)

            # upload attachments
            s3_urls = []
            if uploaded_main:
                uploaded_main.seek(0)
                s3_urls.append(upload_to_s3(uploaded_main, uploaded_main.name))
            for f in uploaded_files:
                f.seek(0)
                s3_urls.append(upload_to_s3(f, f.name))

            st.session_state.update({
                "summary": summary,
                "raw_notes": extra_notes,
                "notes_summary": notes_summary,
                "contacts": contact_info,
                "attachments": s3_urls,
                "deal_type": deal_type_value
            })

# Editable form + upload
if "summary" in st.session_state:
    st.markdown("<h2>Review & Edit Deal Details</h2>", unsafe_allow_html=True)
    
    with st.form("edit_form", clear_on_submit=False):
        s = st.session_state["summary"]
        
        # Property Details
        property_name = st.text_input("Property Name", value=s.get("Property Name",""))
        location = st.text_input("Location", value=s.get("Location",""))
        asset_class = st.text_input("Asset Class", value=s.get("Asset Class",""))
        size = st.text_input("Size (Sq Ft or Unit Count)", value=s.get("Square Footage or Unit Count",""))
        
        # Deal Team
        sponsor = st.text_input("Sponsor", value=s.get("Sponsor",""))
        broker = st.text_input("Broker", value=s.get("Broker",""))
        
        # Financial Details
        purchase_price = st.text_input("Purchase Price", value=s.get("Purchase Price",""))
        loan_amount = st.text_input("Loan Amount", value=s.get("Loan Amount",""))
        in_cap_rate = st.text_input("In-Place Cap Rate", value=s.get("In-Place Cap Rate",""))
        stab_cap_rate = st.text_input("Stabilized Cap Rate", value=s.get("Stabilized Cap Rate",""))
        interest_rate = st.text_input("Interest Rate", value=s.get("Interest Rate",""))
        term = st.text_input("Term", value=s.get("Term",""))
        proj_irr = st.text_input("Projected IRR", value=s.get("Projected IRR",""))
        hold_period = st.text_input("Hold Period", value=s.get("Hold Period",""))
        exit_strategy = st.text_input("Exit Strategy", value=s.get("Exit Strategy",""))

        st.markdown("---")
        
        # Analysis
        key_highlights = st.text_area("Key Highlights", value="\n".join(s.get("Key Highlights",[])), height=120)
        risks = st.text_area("Risks or Red Flags", value="\n".join(s.get("Risks or Red Flags",[])), height=120)
        summary_text = st.text_area("Summary", value=s.get("Summary",""), height=100)
        raw_notes = st.text_area("Raw Notes", value=st.session_state.get("raw_notes",""), height=120)
        
        submitted = st.form_submit_button("Save to Airtable")

    if submitted:
        with st.spinner("📡 Uploading to Airtable…"):
            updated = {
                "Property Name":       property_name,
                "Location":            location,
                "Maps Link":           generate_maps_link(location),
                "Asset Class":         asset_class,
                "Sponsor":             sponsor,
                "Broker":              broker,
                "Purchase Price":      purchase_price,
                "Loan Amount":         loan_amount,
                "In-Place Cap Rate":   in_cap_rate,
                "Stabilized Cap Rate": stab_cap_rate,
                "Interest Rate":       interest_rate,
                "Term":                term,
                "Exit Strategy":       exit_strategy,
                "Projected IRR":       proj_irr,
                "Hold Period":         hold_period,
                "Size":                size,
                "Key Highlights":      key_highlights.strip().split("\n"),
                "Risks or Red Flags":  risks.strip().split("\n"),
                "Summary":             summary_text
            }
            create_airtable_record(
                updated,
                raw_notes,
                st.session_state["attachments"],
                st.session_state["deal_type"],
                st.session_state["contacts"]
            )
        st.success("✅ Deal saved to Airtable!")
