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
import random
import time
import urllib.parse

# --- Custom CSS for Apple-like styling ---
st.set_page_config(
    page_title="DealFlow AI",
    page_icon="🤖",
    layout="centered"
)

st.markdown("""
    <style>
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Remove question mark icons */
        .stDeployButton, .stToolbar {
            display: none !important;
        }
        
        /* Remove header decoration */
        .css-10trblm {
            text-decoration: none !important;
            margin-left: 0 !important;
        }
        .css-10trblm:hover {
            text-decoration: none !important;
        }
        .css-10trblm p {
            color: inherit !important;
        }
        
        /* Remove help icons */
        .help-icon, .css-1vbd788 {
            display: none !important;
        }
        
        /* Hide header links and anchors */
        a.anchor-link {
            display: none !important;
        }
        .css-1vbd788 > a {
            display: none !important;
        }
        
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
        }
        
        h2 {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 600 !important;
            font-size: 1.3rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Form styling */
        .stRadio > label {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        /* Input field styling */
        .stTextInput > label {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        /* Light mode styles */
        @media (prefers-color-scheme: light) {
            body {
                background-color: #FFFFFF;
                color: #1D1D1F;
            }
            
            h1, h2, .stRadio > label, .stTextInput > label {
                color: #1D1D1F !important;
            }
            
            .stTextInput > div > div {
                border: 1px solid #E6E6E6 !important;
                border-radius: 6px !important;
                background-color: #FFFFFF !important;
                color: #1D1D1F !important;
            }
            
            .editable-form {
                background-color: #F8F8FA;
                border: 1px solid #E6E6E6;
            }

            .status-message {
                color: #1D1D1F !important;
            }

            .spinner {
                border: 2px solid rgba(12, 60, 96, 0.2) !important;
                border-top: 2px solid #0c3c60 !important;
            }
        }
        
        /* Dark mode styles */
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #1A1A1A;
                color: #FFFFFF;
            }
            
            h1, h2, .stRadio > label, .stTextInput > label {
                color: #FFFFFF !important;
            }
            
            .stTextInput > div > div {
                border: 1px solid #404040 !important;
                border-radius: 6px !important;
                background-color: #2D2D2D !important;
                color: #FFFFFF !important;
            }
            
            .editable-form {
                background-color: #2D2D2D;
                border: 1px solid #404040;
            }
            
            .stTextArea > div > div {
                background-color: #2D2D2D !important;
                border-color: #404040 !important;
                color: #FFFFFF !important;
            }
            
            .success {
                background-color: #2D2D2D !important;
                color: #FFFFFF !important;
            }
            
            .stForm {
                background-color: #2D2D2D !important;
            }

            .status-message {
                color: #FFFFFF !important;
            }

            .spinner {
                border: 2px solid rgba(255, 255, 255, 0.2) !important;
                border-top: 2px solid #FFFFFF !important;
            }
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
            border: 1px solid #404040;
            border-radius: 6px;
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        /* Success message styling */
        .success {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 0.75rem;
            border-radius: 6px;
            margin: 0.5rem 0;
        }
        
        /* Divider styling */
        hr {
            margin: 1rem 0 !important;
            border: none;
            border-top: 1px solid #404040;
        }
        
        /* Text area styling */
        .stTextArea > label {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .stTextArea > div > div {
            border-radius: 6px !important;
        }
        
        .stTextArea > div > div:hover,
        .stTextInput > div > div:hover {
            border-color: #0c3c60 !important;
            box-shadow: 0 0 0 1px #0c3c60 !important;
        }
        
        .stTextArea > div > div:focus-within,
        .stTextInput > div > div:focus-within {
            border-color: #0c3c60 !important;
            box-shadow: 0 0 0 2px #0c3c60 !important;
        }
        
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: rgba(255, 255, 255, 0.1) !important;
        }
        .stProgress > div > div > div {
            background-color: #0c3c60 !important;
        }
        
        /* Status message styling */
        .status-message {
            font-weight: 500 !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
        }
        
        /* Spinner animation */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .spinner {
            width: 16px !important;
            height: 16px !important;
            border-radius: 50% !important;
            animation: spin 1s linear infinite !important;
            display: inline-block !important;
            margin-right: 8px !important;
        }
        
        /* Back button styling */
        .back-button {
            position: absolute;
            left: -60px;
            top: 0;
            font-size: 24px;
            color: #666;
            text-decoration: none;
            background: none;
            border: none;
            cursor: pointer;
            padding: 10px;
            transition: color 0.2s;
        }
        .back-button:hover {
            color: #333;
        }
        
        /* Container for page content */
        .page-container {
            position: relative;
            margin-left: 20px;
            padding-top: 10px;
        }
        
        /* Success message styling */
        .success-message {
            padding: 16px;
            border-radius: 8px;
            background-color: #f0f9f4;
            border: 1px solid #68d391;
            color: #276749;
            margin: 16px 0;
        }
        
        /* Dark mode adjustments */
        @media (prefers-color-scheme: dark) {
            .back-button {
                color: #999;
            }
            .back-button:hover {
                color: #fff;
            }
            .success-message {
                background-color: #1a332b;
                border-color: #276749;
                color: #68d391;
            }
        }
        
        /* Container for back button and heading */
        .page-header {
            position: relative;
            margin-bottom: 2rem;
        }
        
        /* Back button container */
        .page-header > div:first-child {
            position: absolute;
            left: -40px;
            top: 50%;
            transform: translateY(-50%);
        }
        
        /* Back button styling */
        .stButton > button[kind="secondary"] {
            background-color: transparent !important;
            border: 1px solid #0c3c60 !important;
            color: #0c3c60 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background-color: #0c3c60 !important;
            color: white !important;
            transform: scale(1.02);
        }
        
        /* Dark mode adjustments */
        @media (prefers-color-scheme: dark) {
            .stButton > button[kind="secondary"] {
                border-color: #4a90e2 !important;
                color: #4a90e2 !important;
            }
            .stButton > button[kind="secondary"]:hover {
                background-color: #4a90e2 !important;
                color: #1a1a1a !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- Loading Messages ---
LOADING_MESSAGES = [
    "Reading and extracting text from uploaded documents...",
    "Processing deal memo and notes...",
    "Identifying key deal terms and metrics...",
    "Organizing extracted information...",
    "Preparing data for review..."
]

def get_loading_message(stage: int) -> str:
    """Get appropriate loading message for each stage."""
    messages = {
        0: "Reading and extracting text from documents",
        1: "Processing deal information",
        2: "Extracting contact information",
        3: "Uploading and organizing attachments",
        4: "Preparing final summary"
    }
    return messages.get(stage, "Processing")

# --- Config and Clients ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
AIRTABLE_PAT         = st.secrets["AIRTABLE_PAT"]
AIRTABLE_BASE_ID     = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME  = st.secrets["AIRTABLE_TABLE_NAME"]
AIRTABLE_CONTACTS_TABLE = st.secrets["AIRTABLE_CONTACTS_TABLE"]
AWS_ACCESS_KEY_ID    = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY= st.secrets["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET            = st.secrets["S3_BUCKET"]
S3_REGION            = st.secrets["S3_REGION"]

# Debug Smarty secrets
try:
    # Check if keys exist in secrets
    all_secrets = st.secrets.to_dict()
    
    SMARTY_AUTH_ID = st.secrets.get("SMARTY_AUTH_ID")
    SMARTY_AUTH_TOKEN = st.secrets.get("SMARTY_AUTH_TOKEN")
    
    SMARTY_ENABLED = bool(SMARTY_AUTH_ID and SMARTY_AUTH_TOKEN)
    if not SMARTY_ENABLED:
        st.warning("Smarty API credentials not found in secrets. Address validation will be disabled.")
    
except Exception as e:
    SMARTY_ENABLED = False
    st.warning(f"Error checking Smarty credentials: {str(e)}. Address validation will be disabled.")

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
    
    # Generate a pre-signed URL that's valid for 1 hour
    try:
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': key},
            ExpiresIn=3600  # 1 hour
        )
        return presigned_url
    except Exception as e:
        # Fallback to regular URL if pre-signed fails
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{key}"

def delete_from_s3(s3_url: str):
    """Delete a file from S3 given its URL."""
    try:
        # Extract the key from the S3 URL
        parsed_url = urllib.parse.urlparse(s3_url)
        key = parsed_url.path.lstrip('/')
        
        # Delete the object
        s3.delete_object(Bucket=S3_BUCKET, Key=key)
    except Exception as e:
        st.warning(f"Failed to delete file from S3: {str(e)}")

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

def validate_address(address: str) -> Dict:
    """
    Validate and enrich address using Smarty Property Data API (Principal Edition).
    Returns formatted address and property data.
    """
    if not address or not SMARTY_ENABLED:
        return None
        
    try:
        # Parse address components
        address_parts = address.split(',')
        street = address_parts[0].strip()
        city = address_parts[1].strip() if len(address_parts) > 1 else ""
        state_zip = address_parts[2].strip().split() if len(address_parts) > 2 else ["", ""]
        state = state_zip[0] if state_zip else ""
        zipcode = state_zip[1] if len(state_zip) > 1 else ""

        # Construct API URL with proper encoding
        base_url = "https://us-enrichment.api.smarty.com/lookup/search/property/principal"
        params = {
            "auth-id": SMARTY_AUTH_ID,
            "auth-token": SMARTY_AUTH_TOKEN,
            "street": street,
            "city": city,
            "state": state,
            "zipcode": zipcode
        }
        
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            result = data[0]
            
            # Format the address and extract property data
            property_data = {
                "formatted_address": f"{result['matched_address']['street']}, {result['matched_address']['city']}, {result['matched_address']['state']} {result['matched_address']['zipcode']}",
                "property_type": result.get('attributes', {}).get('land_use_standard', ''),
                "raw_data": result
            }
            return property_data
            
    except requests.exceptions.RequestException as e:
        st.error("Smarty API Error")
        return None
    
    return None

def format_tax_info(address_data):
    """Format tax information from Smarty API response into a readable string."""
    if not address_data or 'raw_data' not in address_data:
        return ""
        
    tax_info = address_data['raw_data']['tax_info']
    
    # Format currency values
    def format_currency(value):
        try:
            if not value:
                return "N/A"
            return f"${float(value):,.2f}"
        except:
            return str(value)
    
    sections = []
    
    # Current Tax Information
    current_tax = tax_info['current_tax']
    if any(current_tax.values()):
        sections.append(f"Current Tax Information:\n" +
                      f"• Tax Year: {current_tax['tax_year']}\n" +
                      f"• Tax Amount: {format_currency(current_tax['tax_amount'])}\n" +
                      f"• Tax Rate Area: {current_tax['tax_rate_area']}\n" +
                      f"• Tax Jurisdiction: {current_tax['tax_jurisdiction']}")

    # Assessment Values
    assessment = tax_info['assessment']
    if any(assessment.values()):
        sections.append(f"Assessment Values:\n" +
                      f"• Total Value: {format_currency(assessment['total_value'])}\n" +
                      f"• Assessed Value: {format_currency(assessment['assessed_value'])}\n" +
                      f"• Land Value: {format_currency(assessment['land_value'])}\n" +
                      f"• Improvement Value: {format_currency(assessment['improvement_value'])}\n" +
                      f"• Improvement %: {assessment['improvement_percent']}%\n" +
                      f"• Assessment Year: {assessment['assessment_year']}\n" +
                      f"• Last Update: {assessment['last_update']}")

    # Market Values
    market = tax_info['market_values']
    if any(market.values()):
        sections.append(f"Market Values:\n" +
                      f"• Total Value: {format_currency(market['total_value'])}\n" +
                      f"• Land Value: {format_currency(market['land_value'])}\n" +
                      f"• Improvement Value: {format_currency(market['improvement_value'])}\n" +
                      f"• Improvement %: {market['improvement_percent']}%\n" +
                      f"• Value Year: {market['value_year']}")

    return "\n\n".join(sections)

def format_ownership_info(address_data):
    """Format ownership information from Smarty API response into a readable string."""
    if not address_data or 'raw_data' not in address_data:
        return ""
        
    ownership = address_data['raw_data']['ownership']
    
    # Format date values
    def format_date(date_str):
        if not date_str:
            return "N/A"
        try:
            # Try to parse and reformat the date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return date_str
    
    lines = []
    
    # Owner Information
    if ownership['owner_name']:
        lines.append(f"• Owner Name: {ownership['owner_name']}")
    
    # Occupancy Status
    if ownership['owner_occupied']:
        lines.append(f"• Owner Occupied: {ownership['owner_occupied']}")
    
    # Sale History
    if ownership['last_sale_date']:
        lines.append(f"• Last Sale Date: {format_date(ownership['last_sale_date'])}")
    
    if ownership['prior_sale_date']:
        lines.append(f"• Prior Sale Date: {format_date(ownership['prior_sale_date'])}")
    
    return "\n".join(lines) if lines else "No ownership information available"

def format_physical_property(result):
    """Format physical property information from Smarty API response."""
    attrs = result.get('attributes', {})
    
    def format_number(value, decimals=2):
        try:
            if not value:
                return "N/A"
            return f"{float(value):,.{decimals}f}"
        except:
            return str(value)
    
    fields = {
        "Acres": format_number(attrs.get('acres')),
        "Building Sqft": format_number(attrs.get('building_sqft'), 0),
        "Number of Buildings": attrs.get('number_of_buildings', 'N/A'),
        "Stories Number": attrs.get('stories_number', 'N/A'),
        "Year Built": attrs.get('year_built', 'N/A')
    }
    
    return "\n".join(f"• {k}: {v}" for k, v in fields.items() if v != "N/A")

def format_parcel_tax_info(result):
    """Format parcel and tax information from Smarty API response."""
    attrs = result.get('attributes', {})
    
    def format_currency(value):
        try:
            if not value:
                return "N/A"
            return f"${float(value):,.2f}"
        except:
            return str(value)
    
    fields = {
        "Parcel Account Number": attrs.get('parcel_account_number', 'N/A'),
        "Parcel Raw Number": attrs.get('parcel_raw_number', 'N/A'),
        "Parcel Number Previous": attrs.get('parcel_number_previous', 'N/A'),
        "Parcel Number Year Added": attrs.get('parcel_number_year_added', 'N/A'),
        "Parcel Number Year Change": attrs.get('parcel_number_year_change', 'N/A'),
        "Previous Assessed Value": format_currency(attrs.get('previous_assessed_value')),
        "Total Market Value": format_currency(attrs.get('total_market_value')),
        "Tax Billed Amount": format_currency(attrs.get('tax_billed_amount')),
        "Tax Assess Year": attrs.get('tax_assess_year', 'N/A'),
        "Tax Fiscal Year": attrs.get('tax_fiscal_year', 'N/A'),
        "Tax Jurisdiction": attrs.get('tax_jurisdiction', 'N/A')
    }
    
    return "\n".join(f"• {k}: {v}" for k, v in fields.items() if v != "N/A")

def format_ownership_sale_info(result):
    """Format ownership and sale information from Smarty API response."""
    attrs = result.get('attributes', {})
    
    def format_date(date_str):
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return str(date_str)
    
    def format_currency(value):
        try:
            if not value:
                return "N/A"
            return f"${float(value):,.2f}"
        except:
            return str(value)
    
    fields = {
        "Owner Full Name": attrs.get('owner_full_name', 'N/A'),
        "Owner Occupancy Status": attrs.get('owner_occupancy_status', 'N/A'),
        "Deed Owner Full Name": attrs.get('deed_owner_full_name', 'N/A'),
        "Deed Owner Last Name": attrs.get('deed_owner_last_name', 'N/A'),
        "Deed Sale Date": format_date(attrs.get('deed_sale_date')),
        "Deed Sale Price": format_currency(attrs.get('deed_sale_price')),
        "Deed Transaction ID": attrs.get('deed_transaction_id', 'N/A'),
        "Ownership Transfer Date": format_date(attrs.get('ownership_transfer_date')),
        "Prior Sale Date": format_date(attrs.get('prior_sale_date')),
        "Sale Date": format_date(attrs.get('sale_date'))
    }
    
    return "\n".join(f"• {k}: {v}" for k, v in fields.items() if v != "N/A")

def format_mortgage_lender_info(result):
    """Format mortgage and lender information from Smarty API response."""
    attrs = result.get('attributes', {})
    
    def format_currency(value):
        try:
            if not value:
                return "N/A"
            return f"${float(value):,.2f}"
        except:
            return str(value)
    
    def format_date(date_str):
        if not date_str:
            return "N/A"
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        except:
            return str(date_str)
    
    fields = {
        "Mortgage Amount": format_currency(attrs.get('mortgage_amount')),
        "Mortgage Recording Date": format_date(attrs.get('mortgage_recording_date')),
        "Mortgage Type": attrs.get('mortgage_type', 'N/A'),
        "Lender Name": attrs.get('lender_name', 'N/A'),
        "Lender Last Name": attrs.get('lender_last_name', 'N/A'),
        "Lender Code 2": attrs.get('lender_code_2', 'N/A'),
        "Lender Address": attrs.get('lender_address', 'N/A'),
        "Lender City": attrs.get('lender_city', 'N/A'),
        "Lender State": attrs.get('lender_state', 'N/A'),
        "Lender Zip": attrs.get('lender_zip', 'N/A')
    }
    
    return "\n".join(f"• {k}: {v}" for k, v in fields.items() if v != "N/A")

def create_airtable_record(
    data: Dict,
    raw_notes: str,
    attachments: List[str],
    deal_type: str,
    contact_info: str
):
    # Always tag new deals as "Pursuing"
    status = "Pursuing"
    
    try:
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT}",
            "Content-Type": "application/json"
        }
        
        # Get location and validate address
        location = data.get("Location", "")
        if location and SMARTY_ENABLED:
            address_data = validate_address(location)
            if address_data:
                # Address validation successful
                validated_location = address_data.get('formatted_address', location)
                maps_link = generate_maps_link(validated_location)
                
                # Format property information using new functions
                result = address_data.get('raw_data', {})
                
                physical_property = format_physical_property(result)
                parcel_tax = format_parcel_tax_info(result)
                ownership_sale = format_ownership_sale_info(result)
                mortgage_lender = format_mortgage_lender_info(result)
            else:
                maps_link = generate_maps_link(location)
                validated_location = location
                physical_property = ""
                parcel_tax = ""
                ownership_sale = ""
                mortgage_lender = ""
        else:
            maps_link = generate_maps_link(location)
            validated_location = location
            physical_property = ""
            parcel_tax = ""
            ownership_sale = ""
            mortgage_lender = ""
        
        fields = {
            "Deal Type": [deal_type],
            "Status": status,
            "Notes": data.get("Notes"),
            "Raw Notes": raw_notes,
            "Contact Info": contact_info,
            "Sponsor": data.get("Sponsor"),
            "Broker": data.get("Broker"),
            "Property Name": data.get("Property Name"),
            "Location": validated_location,
            "Map": maps_link,
            "Public Records": f"𝗣𝗵𝘆𝘀𝗶𝗰𝗮𝗹 𝗣𝗿𝗼𝗽𝗲𝗿𝘁𝘆: \n{physical_property}\n\n𝗢𝘄𝗻𝗲𝗿𝘀𝗵𝗶𝗽 & 𝗦𝗮𝗹𝗲: \n{ownership_sale}\n\n𝗣𝗮𝗿𝗰𝗲𝗹 & 𝗧𝗮𝘅: \n{parcel_tax}\n\n𝗠𝗼𝗿𝘁𝗴𝗮𝗴𝗲 & 𝗟𝗲𝗻𝗱𝗲𝗿: \n{mortgage_lender}",
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
            "Size": data.get("Size"),
        }
        
        # Add attachments with enhanced format
        if attachments:
            attachment_list = []
            for url in attachments:
                # Extract filename from URL
                filename = url.split('/')[-1]
                filename = urllib.parse.unquote(filename)
                
                attachment_list.append({
                    "url": url,
                    "filename": filename
                })
            
            fields["Attachments"] = attachment_list
        
        resp = requests.post(
            f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}",
            headers=headers,
            json={"fields": fields}
        )
        
        if resp.status_code not in (200, 201):
            st.error(f"Airtable error: {resp.text}")
        else:
            st.success("✅ Deal saved to Airtable!")
            # Note: S3 files are not automatically deleted to ensure Airtable can access them
            # You may want to set up a separate cleanup process for old files
    except Exception as e:
        st.error(f"Error creating Airtable record: {str(e)}")

def parse_contact_info(text: str) -> Dict:
    """Parse contact information from text using GPT."""
    prompt = (
        "Extract contact information from the following text block. "
        "Return a JSON object with these fields (leave empty if not found):\n"
        "- Name (full name)\n"
        "- Email\n"
        "- Phone (primary phone number)\n"
        "- Address (full address)\n"
        "- Website\n"
        "- Notes (any additional relevant information)\n\n"
        f"Text:\n{text}"
    )
    
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    try:
        # Clean the response and parse JSON
        content = res.choices[0].message.content
        # Remove any markdown code block syntax
        content = re.sub(r"```(?:json)?", "", content).strip()
        # Remove any text before the first {
        content = re.sub(r"^[^\{]*", "", content, flags=re.DOTALL)
        return json.loads(content)
    except Exception as e:
        st.error(f"Error parsing contact info: {str(e)}")
        return {}

def create_contact_record(
    contact_data: Dict,
    attachments: List[str]
):
    """Create a new record in the Contacts table."""
    try:
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT}",
            "Content-Type": "application/json"
        }
        
        # Format website as URL if it exists and doesn't start with http
        website = contact_data.get("Website", "")
        if website and not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        fields = {
            "Name": contact_data.get("Name", ""),
            "Email": contact_data.get("Email", ""),
            "Phone": contact_data.get("Phone", ""),
            "Address": contact_data.get("Address", ""),
            "Website": website,
            "Notes": contact_data.get("Notes", ""),
            "Attachments": [{"url": u} for u in attachments] if attachments else []
        }
        
        resp = requests.post(
            f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Contacts",
            headers=headers,
            json={"fields": fields}
        )
        
        if resp.status_code not in (200, 201):
            st.error(f"Airtable error: {resp.text}")
            return False
        return True
    except Exception as e:
        st.error(f"Error creating contact: {str(e)}")
        return False

def list_airtable_fields():
    """List all available fields in the Airtable base to help identify field names."""
    try:
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT}",
            "Content-Type": "application/json"
        }
        
        # Get table schema
        resp = requests.get(
            f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables",
            headers=headers
        )
        
        if resp.status_code == 200:
            tables = resp.json().get('tables', [])
            for table in tables:
                if table.get('name') == AIRTABLE_TABLE_NAME:
                    st.info(f"Available fields in '{AIRTABLE_TABLE_NAME}' table:")
                    for field in table.get('fields', []):
                        field_name = field.get('name', '')
                        field_type = field.get('type', '')
                        st.write(f"• {field_name} ({field_type})")
                    return
        else:
            st.error(f"Could not fetch table schema: {resp.text}")
    except Exception as e:
        st.error(f"Error fetching table schema: {str(e)}")

# --- Streamlit UI ---

# Main navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

# Home page with big buttons
if st.session_state.current_page == 'home':
    st.markdown("<h1 style='text-align: center;'>Real Estate AI Tools</h1>", unsafe_allow_html=True)
    
    # Create two columns for the main buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏢 DealFlow AI", key="dealflow_btn", use_container_width=True):
            st.session_state.current_page = 'dealflow'
            st.rerun()
    
    with col2:
        if st.button("📞 Contact AI", key="contact_btn", use_container_width=True):
            st.session_state.current_page = 'contact'
            st.rerun()
    
    with col3:
        if st.button("🏠 Property Info", key="property_btn", use_container_width=True):
            st.session_state.current_page = 'property'
            st.rerun()
    
    # Add descriptions below buttons
    col1.markdown("""
        #### Deal Analysis Tool
        Upload deal memos and supporting documents for instant analysis and organization.
    """)
    
    col2.markdown("""
        #### Contact Management
        Extract and organize contact information from email signatures and business cards.
    """)
    
    col3.markdown("""
        #### Property Research
        Get detailed property information and market data for any address.
    """)

elif st.session_state.current_page == 'dealflow':
    st.markdown("<h1>DealFlow AI</h1>", unsafe_allow_html=True)
    
    if st.button("← Back", key="back_dealflow", type="secondary"):
        st.session_state.current_page = 'home'
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Map display values to Airtable values
    DEAL_TYPE_MAP = {
        "🏢 Equity": "Equity",
        "🏦 Debt": "Debt"
    }
    
    deal_type = st.radio("Select Deal Type", list(DEAL_TYPE_MAP.keys()), horizontal=True, label_visibility="visible")
    
    uploaded_main = st.file_uploader("Upload Deal Memo", type=["pdf","doc","docx"], 
        label_visibility="visible")

    uploaded_files = st.file_uploader(
        "Supporting Documents",
        type=["pdf","doc","docx","xls","xlsx","jpg","png"],
        accept_multiple_files=True,
        label_visibility="visible"
    )

    extra_notes = st.text_area(
        "Deal Notes or Email Thread",
        height=150,
        label_visibility="visible"
    )

    analyze_button = st.button("🚀 Analyze Deal")

    if analyze_button:
        status_container = st.empty()
        try:
            for i in range(5):
                # Update message first
                status_container.markdown(
                    f'<div class="status-message"><div class="spinner"></div>{get_loading_message(i)}</div>',
                    unsafe_allow_html=True
                )
                
                # Add a small delay between messages
                time.sleep(0.5)  # Half second delay between messages
                
                if i == 0:
                    # Initial document processing
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
                
                elif i == 1 and (source_text or extra_notes.strip()):
                    # Process text and generate summary
                    combined = (source_text + "\n\n" + extra_notes).strip()
                    summary = gpt_extract_summary(combined, DEAL_TYPE_MAP[deal_type])
                
                elif i == 2:
                    # Process notes and contact info
                    notes_summary = summarize_notes(extra_notes)
                    contact_info = extract_contact_info(combined)
                
                elif i == 3:
                    # Handle attachments
                    s3_urls = []
                    if uploaded_main:
                        uploaded_main.seek(0)
                        s3_urls.append(upload_to_s3(uploaded_main, uploaded_main.name))
                    for f in uploaded_files:
                        f.seek(0)
                        s3_urls.append(upload_to_s3(f, f.name))
                
                elif i == 4:
                    # Update session state
                    st.session_state.update({
                        "summary": summary,
                        "raw_notes": extra_notes,
                        "notes_summary": notes_summary,
                        "contacts": contact_info,
                        "attachments": s3_urls,
                        "deal_type": DEAL_TYPE_MAP[deal_type] if deal_type else ""  # Map to Airtable value
                    })

                    # Try to validate address from extracted location
                    location = summary.get("Location", "")
                    if location:
                        address_data = validate_address(location)
                        if address_data:
                            # Address validation successful
                            result = address_data.get('raw_data', {})
                            st.session_state.update({
                                "Physical Property": format_physical_property(result),
                                "Parcel & Tax": format_parcel_tax_info(result),
                                "Ownership & Sale": format_ownership_sale_info(result),
                                "Mortgage & Lender": format_mortgage_lender_info(result),
                                "address_validated": True,
                                "address_data": address_data
                            })
                        else:
                            # Address validation failed - will prompt user for manual input
                            st.session_state.update({
                                "address_validated": False,
                                "extracted_location": location
                            })
                    else:
                        # No location extracted - will prompt user for manual input
                        st.session_state.update({
                            "address_validated": False,
                            "extracted_location": ""
                        })

                    # Add another message update right after processing
                    if i < 4:  # Don't update after the last step
                        status_container.markdown(
                            f'<div class="status-message"><div class="spinner"></div>{get_loading_message(i + 1)}</div>',
                            unsafe_allow_html=True
                        )
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        finally:
            status_container.empty()

    # Editable form + upload
    if "summary" in st.session_state:
        st.markdown("<h2>Review & Edit Deal Details</h2>", unsafe_allow_html=True)
        
        # Show address input if validation failed
        manual_address = ""
        if st.session_state.get("address_validated") == False:
            st.markdown("### Address Validation")
            extracted_loc = st.session_state.get("extracted_location", "")
            if extracted_loc:
                st.info(f"Could not validate the extracted address: '{extracted_loc}'. Please provide a valid property address.")
            else:
                st.info("No property address was detected from the documents. Please provide a valid property address.")
            
            manual_address = st.text_input(
                label="Property Address",
                placeholder="e.g., 123 Main St, City, State 12345",
                help="Enter the property address to get detailed property information"
            )
            
            if manual_address.strip():
                if st.button("🔍 Validate Address"):
                    with st.spinner("Validating address..."):
                        address_data = validate_address(manual_address.strip())
                        if address_data:
                            result = address_data.get('raw_data', {})
                            st.session_state.update({
                                "Physical Property": format_physical_property(result),
                                "Parcel & Tax": format_parcel_tax_info(result),
                                "Ownership & Sale": format_ownership_sale_info(result),
                                "Mortgage & Lender": format_mortgage_lender_info(result),
                                "address_validated": True,
                                "address_data": address_data
                            })
                            st.success("Address validated successfully! Property information has been updated.")
                            st.rerun()
                        else:
                            st.error("Could not validate this address. Please check the format and try again.")
        elif st.session_state.get("address_validated") == True:
            pass
        
        with st.form("edit_form", clear_on_submit=False):
            s = st.session_state["summary"]
            
            # Property Details
            property_name = st.text_input("Property Name", value=s.get("Property Name",""))
            # Use validated address if available, otherwise use extracted location
            if st.session_state.get("address_validated") == True:
                # Use the validated address from Smarty
                address_data = st.session_state.get("address_data", {})
                default_location = address_data.get("formatted_address", s.get("Location",""))
            else:
                # Use extracted location or manual address
                default_location = manual_address.strip() if manual_address.strip() else s.get("Location","")
            location = st.text_input("Location", value=default_location)
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
            
            # Analysis - Consolidated Notes
            summary_text = s.get("Summary", "")
            highlights_text = "\n".join(f"• {highlight}" for highlight in s.get("Key Highlights", []) if highlight.strip())
            risks_text = "\n".join(f"• {risk}" for risk in s.get("Risks or Red Flags", []) if risk.strip())
            
            # Create consolidated notes with proper formatting
            consolidated_notes = f"Summary:\n{summary_text}\n\nKey Highlights:\n{highlights_text}\n\nRisks:\n{risks_text}"
            
            notes = st.text_area("Notes", value=consolidated_notes, height=300)
            
            # Create combined Public Records field
            physical_property_text = st.session_state.get("Physical Property", "")
            parcel_tax_text = st.session_state.get("Parcel & Tax", "")
            ownership_sale_text = st.session_state.get("Ownership & Sale", "")
            mortgage_lender_text = st.session_state.get("Mortgage & Lender", "")
            
            combined_public_records = f"𝗣𝗵𝘆𝘀𝗶𝗰𝗮𝗹 𝗣𝗿𝗼𝗽𝗲𝗿𝘁𝘆: \n{physical_property_text}\n\n𝗢𝘄𝗻𝗲𝗿𝘀𝗵𝗶𝗽 & 𝗦𝗮𝗹𝗲: \n{ownership_sale_text}\n\n𝗣𝗮𝗿𝗰𝗲𝗹 & 𝗧𝗮𝘅: \n{parcel_tax_text}\n\n𝗠𝗼𝗿𝘁𝗴𝗮𝗴𝗲 & 𝗟𝗲𝗻𝗱𝗲𝗿: \n{mortgage_lender_text}"
            
            public_records = st.text_area("Public Records", value=combined_public_records, height=400)
            raw_notes = st.text_area("Raw Notes", value=st.session_state.get("raw_notes",""), height=120)
            
            submitted = st.form_submit_button("Save to Airtable")

        if submitted:
            with st.spinner("Saving to Airtable"):
                updated = {
                    "Property Name":       property_name,
                    "Location":            location,
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
                    "Public Records":      public_records,
                    "Notes":               notes
                }
                create_airtable_record(
                    updated,
                    raw_notes,
                    st.session_state["attachments"],
                    DEAL_TYPE_MAP[deal_type],
                    st.session_state["contacts"]
                )

elif st.session_state.current_page == 'contact':
    st.markdown("<h1>Contact AI</h1>", unsafe_allow_html=True)
    if st.button("← Back", key="back_contact", type="secondary"):
        st.session_state.current_page = 'home'
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("Paste a signature block or contact information below, and I'll extract the key details.")
    
    contact_text = st.text_area(
        "Contact Information",
        height=150,
        placeholder="Paste signature block or contact information here...",
        label_visibility="visible"
    )
    
    contact_files = st.file_uploader(
        "Attachments (Optional)",
        type=["pdf","doc","docx","jpg","png"],
        accept_multiple_files=True,
        label_visibility="visible"
    )
    
    parse_clicked = st.button("🔍 Parse Contact")
    
    if parse_clicked and contact_text.strip():
        contact_data = parse_contact_info(contact_text)
        st.session_state.contact_data = contact_data
        st.session_state.show_form = True
        
        # Upload any attachments to S3
        s3_urls = []
        for f in contact_files:
            s3_urls.append(upload_to_s3(f, f.name))
        st.session_state.s3_urls = s3_urls
    elif parse_clicked:
        st.error("Please enter some contact information to parse.")
    
    # Show form if we have parsed data
    if st.session_state.get('show_form', False):
        st.markdown("### Review Parsed Information")
        with st.form("contact_form"):
            contact_data = st.session_state.contact_data
            name = st.text_input("Name", value=contact_data.get("Name", ""))
            email = st.text_input("Email", value=contact_data.get("Email", ""))
            phone = st.text_input("Phone", value=contact_data.get("Phone", ""))
            address = st.text_input("Address", value=contact_data.get("Address", ""))
            website = st.text_input("Website", value=contact_data.get("Website", ""))
            notes = st.text_area("Notes", value=contact_data.get("Notes", ""), height=100)
            
            submitted = st.form_submit_button("Save Contact")
            
            if submitted:
                updated_data = {
                    "Name": name,
                    "Email": email,
                    "Phone": phone,
                    "Address": address,
                    "Website": website,
                    "Notes": notes
                }
                
                success = create_contact_record(updated_data, st.session_state.get('s3_urls', []))
                
                if success:
                    # Delete S3 files after successful save
                    for url in st.session_state.get('s3_urls', []):
                        delete_from_s3(url)
                    st.success("✅ Contact saved to Airtable!")
                    # Clear the form
                    st.session_state.show_form = False
                    st.session_state.contact_data = None
                    st.session_state.s3_urls = []
                else:
                    st.error("Failed to save contact to Airtable. Please try again.")

elif st.session_state.current_page == 'property':
    st.markdown("<h1>Property Info</h1>", unsafe_allow_html=True)
    if st.button("← Back", key="back_property", type="secondary"):
        st.session_state.current_page = 'home'
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("Enter a property address to get detailed information and market data.")
    
    property_address = st.text_input(
        "Property Address",
        placeholder="e.g., 123 Main St, City, State 12345",
        help="Enter the property address to get detailed property information"
    )
    
    if st.button("🔍 Get Property Info", use_container_width=True):
        if property_address.strip():
            with st.spinner("Fetching property information..."):
                address_data = validate_address(property_address.strip())
                if address_data:
                    result = address_data.get('raw_data', {})
                    
                    # Add Google Maps link
                    maps_link = generate_maps_link(address_data.get('formatted_address', property_address))
                    if maps_link:
                        st.markdown(f"📍 [View on Google Maps]({maps_link})")
                    
                    st.markdown("---")
                    
                    # Physical Property Information
                    st.markdown("### Physical Property Information")
                    physical_info = format_physical_property(result)
                    if physical_info:
                        st.text_area("Physical Property Details", value=physical_info, height=150)
                    else:
                        st.info("No physical property information available.")
                    
                    st.markdown("---")
                    
                    # Parcel & Tax Information
                    st.markdown("### Parcel & Tax Information")
                    tax_info = format_parcel_tax_info(result)
                    if tax_info:
                        st.text_area("Tax Details", value=tax_info, height=200)
                    else:
                        st.info("No tax information available.")
                    
                    st.markdown("---")
                    
                    # Ownership & Sale Information
                    st.markdown("### Ownership & Sale Information")
                    ownership_info = format_ownership_sale_info(result)
                    if ownership_info:
                        st.text_area("Ownership Details", value=ownership_info, height=150)
                    else:
                        st.info("No ownership information available.")
                    
                    st.markdown("---")
                    
                    # Mortgage & Lender Information
                    st.markdown("### Mortgage & Lender Information")
                    mortgage_info = format_mortgage_lender_info(result)
                    if mortgage_info:
                        st.text_area("Mortgage Details", value=mortgage_info, height=150)
                    else:
                        st.info("No mortgage information available.")
                else:
                    st.error("Could not validate this address. Please check the format and try again.")
        else:
            st.error("Please enter a property address.")
