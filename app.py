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
import hashlib
import hmac
import base64
import tempfile
import os

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

# OAuth Configuration
GOOGLE_CLIENT_ID = st.secrets.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = st.secrets.get("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "http://localhost:8501")


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

def extract_address_fallback(text: str) -> str:
    """Extract address using a more focused approach when main extraction fails."""
    prompt = (
        "Extract the complete property address from the following text. "
        "Look for addresses that include street number, street name, city, state, and zip code. "
        "Common formats include:\n"
        "- '123 Main St, City, State 12345'\n"
        "- '15031-15139 Marlboro Pike, Upper Marlboro, MD 20772'\n"
        "- '456 Oak Avenue, Springfield, IL 62701'\n\n"
        "Return ONLY the complete address, or 'NOT_FOUND' if no complete address is found.\n\n"
        f"Text:\n{text[:2000]}"
    )
    
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    result = res.choices[0].message.content.strip()
    
    if result and result != "NOT_FOUND" and len(result) > 10:
        return result
    
    return ""

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
    result = res.choices[0].message.content.strip()
    
    # Return blank if no meaningful contact info found
    if not result or "no contact information" in result.lower() or "no brokers" in result.lower():
        return ""
    
    return result

def gpt_extract_summary(text: str, deal_type: str) -> Dict:
    prompt = (
        f"You are an AI real estate analyst reviewing a {deal_type.lower()} opportunity.\n\n"
        f"Text:\n{text[:4000]}\n\n"
        "Return JSON with:\n"
        "- Property Name\n"
        "- Location (extract the COMPLETE property address including street number, street name, city, state, and zip code if available. Look for addresses in formats like '123 Main St, City, State 12345' or '15031-15139 Marlboro Pike, Upper Marlboro, MD 20772')\n"
        "- Asset Class\n"
        "- Sponsor\n"
        "- Broker\n"
        "- Purchase Price\n"
        "- Loan Amount\n"
        "- In-Place Cap Rate\n"
        "- Interest Rate\n"
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
    
    # Clean and format the address for better Google Maps results
    import urllib.parse
    
    # Remove extra whitespace and normalize
    cleaned_address = ' '.join(address.split())
    
    # URL encode the address properly
    encoded_address = urllib.parse.quote(cleaned_address)
    
    return f"https://www.google.com/maps/search/?api=1&query={encoded_address}"

def validate_address(address: str) -> Dict:
    """
    Validate and enrich address using Smarty Property Data API (Principal Edition).
    Returns formatted address and property data.
    """
    if not address or not SMARTY_ENABLED:
        return None
        
    try:
        # Enhanced address parsing to handle various formats
        def parse_address(addr):
            """Parse address into components, handling various formats."""
            addr = addr.strip()
            
            # Handle range addresses like "15031-15139 Marlboro Pike"
            if '-' in addr and any(char.isdigit() for char in addr.split('-')[0]):
                # Extract the first number for the range
                parts = addr.split('-', 1)
                if len(parts) == 2:
                    first_num = parts[0].strip()
                    rest = parts[1].strip()
                    # Use the first number as the street number
                    street = f"{first_num} {rest}"
                else:
                    street = addr
            else:
                street = addr
            
            # Split by comma to get components
            parts = [part.strip() for part in street.split(',')]
            
            if len(parts) >= 3:
                street = parts[0]
                city = parts[1]
                state_zip = parts[2].split()
                state = state_zip[0] if state_zip else ""
                zipcode = state_zip[1] if len(state_zip) > 1 else ""
            elif len(parts) == 2:
                street = parts[0]
                city_state_zip = parts[1].split()
                if len(city_state_zip) >= 3:
                    city = city_state_zip[0]
                    state = city_state_zip[1]
                    zipcode = city_state_zip[2]
                else:
                    city = parts[1]
                    state = ""
                    zipcode = ""
            else:
                # Try to parse single line address
                words = street.split()
                if len(words) >= 4:
                    # Look for state abbreviation (2 letters) and zip (5 digits)
                    for i, word in enumerate(words):
                        if len(word) == 2 and word.isalpha() and i < len(words) - 1:
                            if words[i + 1].isdigit() and len(words[i + 1]) == 5:
                                street = ' '.join(words[:i])
                                city = ' '.join(words[i-1:i]) if i > 0 else ""
                                state = word
                                zipcode = words[i + 1]
                                break
                    else:
                        # Fallback - use first part as street
                        street = words[0] if words else ""
                        city = ' '.join(words[1:]) if len(words) > 1 else ""
                        state = ""
                        zipcode = ""
                else:
                    street = street
                    city = ""
                    state = ""
                    zipcode = ""
            
            return street, city, state, zipcode
        
        street, city, state, zipcode = parse_address(address)

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
        else:
            # If Smarty doesn't find a match, return the original address for Google Maps
            return {
                "formatted_address": address,
                "property_type": "",
                "raw_data": None
            }
            
    except requests.exceptions.RequestException as e:
        st.error("Smarty API Error")
        return None
    except Exception as e:
        # If parsing fails, return the original address
        return {
            "formatted_address": address,
            "property_type": "",
            "raw_data": None
        }
    
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
    if result is None:
        return ""
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
        "Building Sqft": format_number(attrs.get('building_sqft')),
        "Stories Number": attrs.get('stories_number', 'N/A'),
        "Year Built": attrs.get('year_built', 'N/A')
    }
    
    return "\n".join(f"• {k}: {v}" for k, v in fields.items() if v != "N/A")

def format_parcel_tax_info(result):
    """Format parcel and tax information from Smarty API response."""
    if result is None:
        return ""
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
        "Tax Jurisdiction": attrs.get('tax_jurisdiction', 'N/A'),
        "Zoning": attrs.get('zoning', 'N/A'),
        "Land Use": attrs.get('land_use_standard', 'N/A')
    }
    
    return "\n".join(f"• {k}: {v}" for k, v in fields.items() if v != "N/A")

def format_ownership_sale_info(result):
    """Format ownership and sale information from Smarty API response."""
    if result is None:
        return ""
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
    if result is None:
        return ""
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
    
    def format_percentage(value):
        try:
            if not value:
                return "N/A"
            return f"{float(value):.2f}%"
        except:
            return str(value) if value else "N/A"
    
    fields = {
        "Mortgage Amount": format_currency(attrs.get('mortgage_amount')),
        "Mortgage Recording Date": format_date(attrs.get('mortgage_recording_date')),
        "Mortgage Type": attrs.get('mortgage_type', 'N/A'),
        "Mortgage Interest Type": attrs.get('mortgage_interest_type', 'N/A'),
        "Interest Rate": format_percentage(attrs.get('interest_rate')),
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
    
    # Add null checks
    if data is None:
        st.error("Error: Data parameter is None")
        return
    
    if contact_info is None:
        contact_info = ""
    
    if attachments is None:
        attachments = []
    
    if raw_notes is None:
        raw_notes = ""
    
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
            "Type": deal_type,
            "Status": status,
            "Notes": data.get("Notes") if data else "",
            "Raw Notes": raw_notes,
            "Contact Info": contact_info,
            "Sponsor": data.get("Sponsor") if data else "",
            "Broker": data.get("Broker") if data else "",
            "Property Name": data.get("Property Name") if data else "",
            "Location": validated_location,
            "Map": maps_link,
            "Public Records": f"𝗣𝗵𝘆𝘀𝗶𝗰𝗮𝗹 𝗣𝗿𝗼𝗽𝗲𝗿𝘁𝘆: \n{physical_property}\n\n𝗢𝘄𝗻𝗲𝗿𝘀𝗵𝗶𝗽 & 𝗦𝗮𝗹𝗲: \n{ownership_sale}\n\n𝗣𝗮𝗿𝗰𝗲𝗹 & 𝗧𝗮𝘅: \n{parcel_tax}\n\n𝗠𝗼𝗿𝘁𝗴𝗮𝗴𝗲 & 𝗟𝗲𝗻𝗱𝗲𝗿: \n{mortgage_lender}",
            "Asset Class": data.get("Asset Class") if data else "",
            "Purchase Price": data.get("Purchase Price") if data else "",
            "Loan Amount": data.get("Loan Amount") if data else "",
            "In-Place Cap Rate": data.get("In-Place Cap Rate") if data else "",
            "Interest Rate": data.get("Interest Rate") if data else "",
            "Size": data.get("Size") if data else "",
            "Unit Pricing": data.get("Unit Pricing") if data else "",
            "Status Detail": data.get("Status Detail") if data else "",
        }
        
        # Add Owners field if user is selected
        if st.session_state.get('selected_user'):
            fields["Owners"] = [st.session_state['selected_user']]
        
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
            
            # Add link to view in Airtable - use custom URL if available
            deals_url = st.session_state.get('deals_pipeline_url', 'https://airtable.com/appvfD3RKkfDQ6f8j/tblS3TYknfDGYArnc/viwRajkGcrF0dCzDD?blocks=hide')
            if not deals_url:
                deals_url = 'https://airtable.com/appvfD3RKkfDQ6f8j/tblS3TYknfDGYArnc/viwRajkGcrF0dCzDD?blocks=hide'
            
            st.markdown(f"""
            <div style="text-align: center; margin: 15px 0;">
                <a href="{deals_url}" 
                   target="_blank" 
                   style="display: inline-block; background-color: #18BFFF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    📊 View in Airtable
                </a>
            </div>
            """, unsafe_allow_html=True)
            
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
        "- Organization (company or organization name)\n"
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

def parse_multiple_contacts(text: str) -> List[Dict]:
    """Parse multiple contacts from text using GPT."""
    prompt = (
        "Extract multiple contacts from the following text block. "
        "The text may contain multiple people's contact information separated by sections, paragraphs, or other delimiters. "
        "Return a JSON array where each element is a contact object with these fields (leave empty if not found):\n"
        "- Name (full name)\n"
        "- Email\n"
        "- Phone (primary phone number)\n"
        "- Address (full address)\n"
        "- Website\n"
        "- Organization (company or organization name)\n"
        "- Notes (any additional relevant information)\n\n"
        "If there's only one contact, return an array with one element. "
        "If no contacts are found, return an empty array.\n\n"
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
        # Remove any text before the first [
        content = re.sub(r"^[^\[]*", "", content, flags=re.DOTALL)
        parsed_contacts = json.loads(content)
        
        # Ensure it's a list
        if isinstance(parsed_contacts, dict):
            parsed_contacts = [parsed_contacts]
        elif not isinstance(parsed_contacts, list):
            parsed_contacts = []
            
        return parsed_contacts
    except Exception as e:
        st.error(f"Error parsing multiple contacts: {str(e)}")
        return []

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
            "Org": contact_data.get("Organization", ""),
            "Notes": contact_data.get("Notes", ""),
            "Attachments": [{"url": u} for u in attachments] if attachments else []
        }
        
        # Add Owners field if user is selected
        if st.session_state.get('selected_user'):
            fields["Owners"] = [st.session_state['selected_user']]
        
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

def create_multiple_contact_records(contacts: List[Dict], attachments: List[str]) -> Dict[str, int]:
    """Create multiple contact records in Airtable and return success/failure counts."""
    success_count = 0
    failure_count = 0
    
    for i, contact_data in enumerate(contacts):
        try:
            success = create_contact_record(contact_data, attachments)
            if success:
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            st.error(f"Error creating contact {i+1}: {str(e)}")
            failure_count += 1
    
    return {"success": success_count, "failure": failure_count}


def generate_oauth_url():
    """Generate Google OAuth URL."""
    if not GOOGLE_CLIENT_ID:
        return None
    
    # Generate state parameter for security - use a more stable approach
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Store state in session state
    st.session_state.oauth_state = state
    
    # Also store in a simple file-based cache as backup
    try:
        import tempfile
        import os
        cache_file = os.path.join(tempfile.gettempdir(), f"oauth_state_{hash(state) % 10000}.txt")
        with open(cache_file, 'w') as f:
            f.write(state)
    except Exception as e:
        st.write(f"Warning: Could not create state cache: {e}")
    
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid email profile',
        'response_type': 'code',
        'state': state,
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
    if not GOOGLE_CLIENT_SECRET:
        return None
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        return response.json()
    return None

def get_user_info(access_token):
    """Get user information from Google."""
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(user_info_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def find_user_in_airtable(user_info):
    """Find existing user in Airtable. Only existing users are allowed to login."""
    try:
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT}",
            "Content-Type": "application/json"
        }
        
        # First, check if Team table is accessible
        test_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Team"
        test_response = requests.get(test_url, headers=headers, params={'maxRecords': 1})
        if test_response.status_code != 200:
            st.error(f"Cannot access Team table. Please check if the 'Team' table exists in your Airtable base. Error: {test_response.text}")
            return None
        
        # Search for existing user by email
        search_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Team"
        params = {
            'filterByFormula': f"{{Email}} = '{user_info.get('email', '')}'"
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('records'):
                # User exists, return their info
                record = data['records'][0]
                return {
                    'id': record['id'],
                    'name': record['fields'].get('Name', user_info.get('name', '')),
                    'email': record['fields'].get('Email', user_info.get('email', '')),
                    'deals_pipeline_url': record['fields'].get('Deals Pipeline', ''),
                    'contacts_list_url': record['fields'].get('Contacts List', '')
                }
            else:
                # User not found in Team table
                return None
        else:
            return None
        
    except Exception as e:
        st.error(f"Error searching for user in Airtable: {str(e)}")
        return None

def logout_user():
    """Logout the current user and clear session state."""
    # Set logout flag to prevent OAuth processing
    st.session_state.logout_requested = True
    
    # Clear session state
    for key in ['authenticated', 'user_info', 'selected_user', 'selected_user_name', 'oauth_state']:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear OAuth-related URL parameters completely
    st.query_params.clear()
    
    # Clean up any cache files
    try:
        import tempfile
        import os
        import glob
        temp_dir = tempfile.gettempdir()
        state_files = glob.glob(os.path.join(temp_dir, "oauth_state_*.txt"))
        for state_file in state_files:
            try:
                os.remove(state_file)
            except:
                pass
    except:
        pass
    
    # Clear the logout flag after cleanup
    if 'logout_requested' in st.session_state:
        del st.session_state['logout_requested']
    
    st.rerun()

def fetch_users():
    """Fetch list of users from the Team table."""
    try:
        headers = {
            "Authorization": f"Bearer {AIRTABLE_PAT}",
            "Content-Type": "application/json"
        }
        
        # Fetch all records from Team table
        resp = requests.get(
            f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Team",
            headers=headers
        )
        
        if resp.status_code == 200:
            data = resp.json()
            users = []
            for record in data.get('records', []):
                # Extract user name and record ID
                fields = record.get('fields', {})
                user_name = fields.get('Name', '')
                if user_name:
                    users.append({
                        'id': record['id'],
                        'name': user_name
                    })
            return users
        else:
            st.error(f"Could not fetch users: {resp.text}")
            return []
    except Exception as e:
        st.error(f"Error fetching users: {str(e)}")
        return []

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

# Initialize session state variables
if 'show_contacts_form' not in st.session_state:
    st.session_state.show_contacts_form = False
if 'contacts' not in st.session_state:
    st.session_state.contacts = ""
if 'parsing_mode' not in st.session_state:
    st.session_state.parsing_mode = None
if 's3_urls' not in st.session_state:
    st.session_state.s3_urls = []
if 'attachments' not in st.session_state:
    st.session_state.attachments = []
if 'raw_notes' not in st.session_state:
    st.session_state.raw_notes = ""
if 'selected_user' not in st.session_state:
    st.session_state.selected_user = None
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'oauth_state' not in st.session_state:
    st.session_state.oauth_state = None

# OAuth Authentication Check
# Clear logout flag if it exists (from previous logout)
if 'logout_requested' in st.session_state:
    del st.session_state['logout_requested']

if not st.session_state.authenticated:
    # Check if we have OAuth credentials
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        st.error("OAuth not configured. Please add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to your secrets.")
        st.stop()
    
    # Check for OAuth callback
    query_params = st.query_params
    if 'code' in query_params and 'state' in query_params and not st.session_state.get('logout_requested', False):
        # Verify state parameter with better error handling
        received_state = query_params['state']
        
        # Try to get stored state from multiple sources
        stored_state = st.session_state.get('oauth_state')
        
        # If session state is lost, try to recover from file cache
        if not stored_state:
            try:
                import tempfile
                import os
                import glob
                # Look for any oauth state files
                temp_dir = tempfile.gettempdir()
                state_files = glob.glob(os.path.join(temp_dir, "oauth_state_*.txt"))
                
                for state_file in state_files:
                    try:
                        with open(state_file, 'r') as f:
                            cached_state = f.read().strip()
                            if cached_state == received_state:
                                stored_state = cached_state
                                st.session_state.oauth_state = stored_state
                                # Clean up the cache file
                                os.remove(state_file)
                                break
                    except:
                        continue
            except Exception as e:
                pass
        
        if not stored_state:
            st.error("OAuth session expired. Please try signing in again.")
            
            # Add clear cache button
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("🔄 Clear Cache & Try Again", type="primary"):
                    # Clear all OAuth-related session state
                    for key in ['oauth_state', 'authenticated', 'user_info', 'selected_user', 'selected_user_name']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Clear URL parameters
                    st.query_params.clear()
                    
                    # Clean up cache files
                    try:
                        import tempfile
                        import os
                        import glob
                        temp_dir = tempfile.gettempdir()
                        state_files = glob.glob(os.path.join(temp_dir, "oauth_state_*.txt"))
                        for state_file in state_files:
                            try:
                                os.remove(state_file)
                            except:
                                pass
                    except:
                        pass
                    
                    st.rerun()
            with col2:
                if st.button("🏠 Back to Login", type="secondary"):
                    st.query_params.clear()
                    st.rerun()
            
            st.stop()
        elif received_state != stored_state:
            st.error("Invalid OAuth state. This may be due to a security issue or session timeout. Please try signing in again.")
            
            # Add clear cache button
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("🔄 Clear Cache & Try Again", type="primary", key="clear_cache_invalid"):
                    # Clear all OAuth-related session state
                    for key in ['oauth_state', 'authenticated', 'user_info', 'selected_user', 'selected_user_name']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Clear URL parameters
                    st.query_params.clear()
                    
                    # Clean up cache files
                    try:
                        import tempfile
                        import os
                        import glob
                        temp_dir = tempfile.gettempdir()
                        state_files = glob.glob(os.path.join(temp_dir, "oauth_state_*.txt"))
                        for state_file in state_files:
                            try:
                                os.remove(state_file)
                            except:
                                pass
                    except:
                        pass
                    
                    st.rerun()
            with col2:
                if st.button("🏠 Back to Login", type="secondary", key="back_to_login_invalid"):
                    st.query_params.clear()
                    st.rerun()
            
            st.stop()
        
        # Exchange code for token
        with st.spinner("Authenticating..."):
            token_data = exchange_code_for_token(query_params['code'])
            if token_data:
                # Get user info
                user_info = get_user_info(token_data['access_token'])
                if user_info:
                    # Find existing user in Airtable
                    airtable_user = find_user_in_airtable(user_info)
                    if airtable_user:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_info
                        st.session_state.selected_user = airtable_user['id']
                        st.session_state.selected_user_name = airtable_user['name']
                        st.session_state.deals_pipeline_url = airtable_user.get('deals_pipeline_url', '')
                        st.session_state.contacts_list_url = airtable_user.get('contacts_list_url', '')
                        st.success(f"✅ Welcome, {airtable_user['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Access Denied: Your email address is not authorized to access this application. Please contact your administrator to be added to the Team table.")
                else:
                    st.error("Failed to get user information.")
            else:
                st.error("Failed to authenticate with Google.")
    
    # Show login page with clean layout
    # Add hero image
    try:
        st.image("https://raw.githubusercontent.com/ajgreenberg/DealsParser/main/images/DealFlowAI%20Hero.png", use_container_width=True)
    except:
        # Fallback if image not found
        st.markdown("![DealFlow AI Hero](https://raw.githubusercontent.com/ajgreenberg/DealsParser/main/images/DealFlowAI%20Hero.png)")
    
    # Login section below hero image - centered and compact
    st.markdown("""
    <div style="text-align: center; margin: 15px 0;">
        <h3 style="margin-bottom: 5px;">🔐 Sign In</h3>
        <p style="margin-bottom: 15px; color: #666;">Access your DealFlow AI tools</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a retry button if there was an OAuth error
    if 'code' in query_params and 'state' in query_params:
        if st.button("🔄 Try Again", type="secondary", use_container_width=True):
            # Clear OAuth state from session
            if 'oauth_state' in st.session_state:
                del st.session_state['oauth_state']
            
            # Clear OAuth-related URL parameters
            current_params = st.query_params.to_dict()
            params_to_remove = ['code', 'state', 'oauth_state']
            for param in params_to_remove:
                if param in current_params:
                    del current_params[param]
            st.query_params.update(**current_params)
            
            # Clean up any cache files
            try:
                import tempfile
                import os
                import glob
                temp_dir = tempfile.gettempdir()
                state_files = glob.glob(os.path.join(temp_dir, "oauth_state_*.txt"))
                for state_file in state_files:
                    try:
                        os.remove(state_file)
                    except:
                        pass
            except:
                pass
            
            st.rerun()
    
    oauth_url = generate_oauth_url()
    if oauth_url:
        # Make the login button more prominent and centered
        st.markdown(f"""
        <div style="text-align: center; margin: 10px 0;">
            <a href="{oauth_url}" onclick="window.close();" style="display: inline-block; background-color: #4285f4; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <img src="https://developers.google.com/identity/images/g-logo.png" style="width: 20px; height: 20px; margin-right: 8px; vertical-align: middle;">
                Sign in with Google
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("OAuth configuration error. Please check your Google OAuth settings.")
    
    st.stop()

# Home page with big buttons (only shown if authenticated)
if st.session_state.current_page == 'home':
    st.markdown("<h1 style='text-align: center;'>DealFlow AI</h1>", unsafe_allow_html=True)
    
    # Show current user and logout option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"👤 Logged in as: {st.session_state.selected_user_name}")
    with col2:
        if st.button("🚪 Logout", type="secondary"):
            logout_user()
    
    st.markdown("---")
    
    # Create three columns for the main buttons
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
    
    # Show current user and logout option
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get('selected_user_name'):
            st.info(f"👤 Logged in as: {st.session_state['selected_user_name']}")
    with col2:
        if st.button("🚪 Logout", key="logout_dealflow", type="secondary"):
            logout_user()
    
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
                    # Initial document processing - extract text from ALL documents
                    source_text = ""
                    supporting_text = ""
                    
                    # Extract text from main uploaded document
                    if uploaded_main:
                        ext = uploaded_main.name.lower().rsplit(".",1)[-1]
                        if ext == "pdf":
                            source_text = extract_text_from_pdf(uploaded_main)
                        elif ext == "docx":
                            source_text = extract_text_from_docx(uploaded_main)
                        else:
                            uploaded_main.seek(0)
                            source_text = extract_text_from_doc(uploaded_main)
                    
                    # Extract text from all supporting documents
                    if uploaded_files:
                        supporting_texts = []
                        for f in uploaded_files:
                            try:
                                f.seek(0)  # Reset file pointer
                                ext = f.name.lower().rsplit(".",1)[-1]
                                if ext == "pdf":
                                    doc_text = extract_text_from_pdf(f)
                                elif ext == "docx":
                                    doc_text = extract_text_from_docx(f)
                                elif ext in ["doc", "txt"]:
                                    doc_text = extract_text_from_doc(f)
                                else:
                                    doc_text = f"Document: {f.name} (unsupported format)"
                                
                                if doc_text.strip():
                                    supporting_texts.append(f"--- {f.name} ---\n{doc_text}")
                            except Exception as e:
                                supporting_texts.append(f"--- {f.name} ---\nError reading file: {str(e)}")
                        
                        if supporting_texts:
                            supporting_text = "\n\n".join(supporting_texts)
                    
                    # Combine ALL information: main document + supporting documents + deal notes
                    combined = ""
                    all_texts = []
                    
                    if source_text.strip():
                        all_texts.append(f"--- Main Document ---\n{source_text}")
                    if supporting_text.strip():
                        all_texts.append(f"--- Supporting Documents ---\n{supporting_text}")
                    if extra_notes.strip():
                        all_texts.append(f"--- Deal Notes/Email Thread ---\n{extra_notes}")
                    
                    if all_texts:
                        combined = "\n\n".join(all_texts)
                        
                        # Show what was processed
                        st.info(f"📚 **Processing {len(all_texts)} information source(s):**")
                        if source_text.strip():
                            st.write(f"• Main Document ({len(source_text)} characters)")
                        if supporting_text.strip():
                            st.write(f"• Supporting Documents ({len(supporting_text)} characters)")
                        if extra_notes.strip():
                            st.write(f"• Deal Notes/Email Thread ({len(extra_notes)} characters)")
                        st.write(f"**Total combined text: {len(combined)} characters**")
                
                elif i == 1 and combined.strip():
                    # Process text and generate summary
                    summary = gpt_extract_summary(combined, DEAL_TYPE_MAP[deal_type])
                
                elif i == 2 and combined.strip():
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
                    
                    # If location is incomplete or missing, try fallback extraction
                    if not location or len(location.split()) < 3:
                        st.info("🔍 Trying enhanced address extraction...")
                        fallback_address = extract_address_fallback(combined)
                        if fallback_address:
                            location = fallback_address
                            st.success(f"✅ Found address: {location}")
                    
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
            interest_rate = st.text_input("Interest Rate", value=s.get("Interest Rate",""))
            
            # Unit Pricing Calculation
            def calculate_unit_pricing(purchase_price, loan_amount, size):
                """Calculate unit pricing based on purchase price or loan amount and size."""
                try:
                    # Extract numeric values from strings
                    def extract_number(text):
                        if not text:
                            return None
                        # Remove common currency symbols and commas
                        cleaned = re.sub(r'[$,]', '', str(text))
                        # Extract first number found
                        numbers = re.findall(r'[\d,]+\.?\d*', cleaned)
                        if numbers:
                            return float(numbers[0].replace(',', ''))
                        return None
                    
                    price_num = extract_number(purchase_price)
                    loan_num = extract_number(loan_amount)
                    size_num = extract_number(size)
                    
                    if size_num and size_num > 0:
                        if price_num and price_num > 0:
                            return f"${price_num/size_num:.2f} PSF"
                        elif loan_num and loan_num > 0:
                            return f"${loan_num/size_num:.2f} PSF Loan Basis"
                    return "N/A"
                except:
                    return "N/A"
            
            unit_pricing = calculate_unit_pricing(purchase_price, loan_amount, size)
            unit_pricing = st.text_input("Unit Pricing", value=unit_pricing, help="Automatically calculated as Purchase Price ÷ Square Footage (or Loan Amount ÷ Square Footage for loan basis). You can edit this value if needed.")
            
            # Status Detail
            status_detail = st.text_input("Status Detail", value="", placeholder="Enter additional status details...")

            st.markdown("---")
            
            # Analysis - Consolidated Notes
            summary_text = s.get("Summary", "")
            highlights_text = "\n".join(f"• {highlight}" for highlight in s.get("Key Highlights", []) if highlight.strip())
            risks_text = "\n".join(f"• {risk}" for risk in s.get("Risks or Red Flags", []) if risk.strip())
            exit_strategy_text = s.get("Exit Strategy", "")
            
            # Create consolidated notes with proper formatting
            consolidated_notes = f"𝗦𝘂𝗺𝗺𝗮𝗿𝘆:\n{summary_text}\n\n𝗞𝗲𝘆 𝗛𝗶𝗴𝗵𝗹𝗶𝗴𝗵𝘁𝘀:\n{highlights_text}\n\n𝗥𝗶𝘀𝗸𝘀:\n{risks_text}\n\n𝗘𝘅𝗶𝘁 𝗦𝘁𝗿𝗮𝘁𝗲𝗴𝘆:\n{exit_strategy_text}"
            
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
                    "Interest Rate":       interest_rate,
                    "Size":                size,
                    "Unit Pricing":        unit_pricing,
                    "Status Detail":       status_detail,
                    "Public Records":      public_records,
                    "Notes":               notes
                }
                
                # Ensure all parameters are not None
                raw_notes = st.session_state.get("raw_notes", "")
                attachments = st.session_state.get("attachments", [])
                contacts = st.session_state.get("contacts", "")
                
                create_airtable_record(
                    updated,
                    raw_notes,
                    attachments,
                    DEAL_TYPE_MAP[deal_type],
                    contacts
                )

elif st.session_state.current_page == 'contact':
    st.markdown("<h1>Contact AI</h1>", unsafe_allow_html=True)
    
    # Show current user and logout option
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get('selected_user_name'):
            st.info(f"👤 Logged in as: {st.session_state['selected_user_name']}")
    with col2:
        if st.button("🚪 Logout", key="logout_contact", type="secondary"):
            logout_user()
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back", key="back_contact", type="secondary"):
            st.session_state.current_page = 'home'
            st.rerun()
    with col2:
        if st.button("🔄 Parse New Contacts", key="reset_contact", type="secondary"):
            st.session_state.show_contacts_form = False
            st.session_state.contacts = []
            st.session_state.parsing_mode = None
            st.session_state.s3_urls = []
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("Paste contact information or upload a document, and I'll extract all contacts automatically.")
    
    contact_text = st.text_area(
        "Contact Information",
        height=200,
        placeholder="Paste signature blocks, multiple contacts, or any contact information here...",
        label_visibility="visible"
    )
    
    contact_files = st.file_uploader(
        "Document with Contacts (Optional)",
        type=["pdf","doc","docx","txt"],
        accept_multiple_files=False,
        label_visibility="visible",
        help="Supported formats: PDF, DOC, DOCX, TXT. Images (JPG/PNG) are not supported for text extraction."
    )
    
    parse_clicked = st.button("🔍 Parse Contacts", use_container_width=True)
    
    if parse_clicked:
        # Check if we have either text input or a file uploaded
        has_text = contact_text.strip() != ""
        has_file = False
        file_text = ""
        
        # Safely check if we have a valid file
        try:
            # Handle both single file and list of files
            if contact_files:
                if hasattr(contact_files, '__iter__') and not hasattr(contact_files, 'name'):
                    # It's a list/iterable of files
                    if len(contact_files) > 0:
                        file = contact_files[0]
                        has_file = True
                else:
                    # It's a single file object
                    file = contact_files
                    has_file = True
                
                if has_file:
                    try:
                        if file.name.lower().endswith('.pdf'):
                            file_text = extract_text_from_pdf(file)
                        elif file.name.lower().endswith('.docx'):
                            file_text = extract_text_from_docx(file)
                        elif file.name.lower().endswith('.doc'):
                            file_text = extract_text_from_doc(file)
                        elif file.name.lower().endswith('.txt'):
                            file_text = file.read().decode('utf-8')
                        else:
                            st.error(f"Unsupported file type: {file.name}")
                            st.stop()
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                        st.stop()
        except (TypeError, AttributeError) as e:
            # contact_files is None or doesn't support expected operations
            has_file = False
            file_text = ""
        
        if has_text or has_file:
            # Combine file text with pasted text
            if has_text and has_file:
                combined_text = (contact_text + "\n\n" + file_text).strip()
            elif has_text:
                combined_text = contact_text.strip()
            else:
                combined_text = file_text.strip()
            
            if combined_text:
                with st.spinner("Parsing contacts..."):
                    try:
                        # Try to parse as multiple contacts first
                        contacts_data = parse_multiple_contacts(combined_text)
                        
                        if contacts_data and len(contacts_data) > 1:
                            # Multiple contacts found
                            st.session_state.contacts = contacts_data
                            st.session_state.show_contacts_form = True
                            st.session_state.parsing_mode = "multiple"
                            st.success(f"✅ Found {len(contacts_data)} contacts!")
                        elif contacts_data and len(contacts_data) == 1:
                            # Single contact found
                            st.session_state.contacts = contacts_data
                            st.session_state.show_contacts_form = True
                            st.session_state.parsing_mode = "single"
                            st.success("✅ Found 1 contact!")
                        else:
                            st.error("No contacts could be parsed from the provided text.")
                    except Exception as e:
                        st.error(f"Error parsing contacts: {str(e)}")
            else:
                st.error("Please provide contact information to parse.")
        else:
            st.error("Please enter contact information or upload a document to parse.")
    
    # Show unified form for all parsed contacts
    if st.session_state.get('show_contacts_form', False):
        contacts = st.session_state.contacts
        is_multiple = len(contacts) > 1
        
        if is_multiple:
            st.markdown(f"### Review {len(contacts)} Contacts")
            st.markdown("Edit any fields and remove contacts you don't want to save.")
            
            # Handle contact removal outside the form
            for i, contact in enumerate(contacts):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**Contact {i+1}: {contact.get('Name', 'Unnamed')}**")
                with col2:
                    if st.button(f"🗑️ Remove", key=f"remove_{i}", type="secondary"):
                        # Remove this contact from the list
                        contacts.pop(i)
                        st.session_state.contacts = contacts
                        if len(contacts) == 0:
                            st.session_state.show_contacts_form = False
                        st.rerun()
        else:
            st.markdown("### Review Contact")
        
        # Create editable form for contacts
        with st.form("contacts_form"):
            updated_contacts = []
            
            for i, contact in enumerate(contacts):
                st.markdown(f"--- **Contact {i+1}** ---")
                
                # Editable fields
                name = st.text_input("Name", value=contact.get("Name", ""), key=f"name_{i}")
                email = st.text_input("Email", value=contact.get("Email", ""), key=f"email_{i}")
                phone = st.text_input("Phone", value=contact.get("Phone", ""), key=f"phone_{i}")
                address = st.text_input("Address", value=contact.get("Address", ""), key=f"addr_{i}")
                website = st.text_input("Website", value=contact.get("Website", ""), key=f"website_{i}")
                organization = st.text_input("Organization", value=contact.get("Organization", ""), key=f"org_{i}")
                notes = st.text_area("Notes", value=contact.get("Notes", ""), height=80, key=f"notes_{i}")
                
                # Store updated contact data
                updated_contact = {
                    "Name": name,
                    "Email": email,
                    "Phone": phone,
                    "Address": address,
                    "Website": website,
                    "Organization": organization,
                    "Notes": notes
                }
                updated_contacts.append(updated_contact)
                
                st.markdown("---")
            
            # Submit button
            if len(updated_contacts) > 0:
                # Validate that contacts have at least a name
                valid_contacts = [c for c in updated_contacts if c.get('Name', '').strip()]
                invalid_count = len(updated_contacts) - len(valid_contacts)
                
                if invalid_count > 0:
                    st.warning(f"⚠️ {invalid_count} contact(s) are missing names and will be skipped.")
                
                if len(valid_contacts) == 0:
                    st.error("❌ No valid contacts to save. All contacts must have names.")
                    st.stop()
                
                submit_text = f"💾 Save {len(valid_contacts)} Contact(s) to Airtable"
                if is_multiple:
                    submit_text = f"💾 Save {len(valid_contacts)} Valid Contact(s) to Airtable"
                
                submitted = st.form_submit_button(submit_text)
                
                if submitted:
                    # Update session state with edited contacts
                    st.session_state.contacts = updated_contacts
                    
                    with st.spinner("Saving contacts to Airtable..."):
                        if len(valid_contacts) == 1:
                            # Single contact - use single contact function
                            success = create_contact_record(valid_contacts[0], st.session_state.get('s3_urls', []))
                            if success:
                                st.success("✅ Contact saved to Airtable!")
                                
                                # Add link to view in Airtable - use custom URL if available
                                contacts_url = st.session_state.get('contacts_list_url', 'https://airtable.com/appvfD3RKkfDQ6f8j/tbl3EY7dpNcyBo6qG/viwLn1h08dtcJA62V?blocks=hide')
                                if not contacts_url:
                                    contacts_url = 'https://airtable.com/appvfD3RKkfDQ6f8j/tbl3EY7dpNcyBo6qG/viwLn1h08dtcJA62V?blocks=hide'
                                
                                st.markdown(f"""
                                <div style="text-align: center; margin: 15px 0;">
                                    <a href="{contacts_url}" 
                                       target="_blank" 
                                       style="display: inline-block; background-color: #18BFFF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        📊 View in Airtable
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Clear the form
                                st.session_state.show_contacts_form = False
                                st.session_state.contacts = []
                                st.session_state.parsing_mode = None
                                st.session_state.s3_urls = []
                            else:
                                st.error("Failed to save contact to Airtable. Please try again.")
                        else:
                            # Multiple contacts - use bulk function
                            result = create_multiple_contact_records(valid_contacts, [])
                            
                            if result["success"] > 0:
                                st.success(f"✅ Successfully saved {result['success']} contact(s) to Airtable!")
                                
                                # Add link to view in Airtable - use custom URL if available
                                contacts_url = st.session_state.get('contacts_list_url', 'https://airtable.com/appvfD3RKkfDQ6f8j/tbl3EY7dpNcyBo6qG/viwLn1h08dtcJA62V?blocks=hide')
                                if not contacts_url:
                                    contacts_url = 'https://airtable.com/appvfD3RKkfDQ6f8j/tbl3EY7dpNcyBo6qG/viwLn1h08dtcJA62V?blocks=hide'
                                
                                st.markdown(f"""
                                <div style="text-align: center; margin: 15px 0;">
                                    <a href="{contacts_url}" 
                                       target="_blank" 
                                       style="display: inline-block; background-color: #18BFFF; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        📊 View in Airtable
                                    </a>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if result["failure"] > 0:
                                    st.warning(f"⚠️ {result['failure']} contact(s) failed to save.")
                                
                                # Clear the form
                                st.session_state.show_contacts_form = False
                                st.session_state.contacts = []
                                st.session_state.parsing_mode = None
                            else:
                                st.error("❌ Failed to save any contacts to Airtable. Please try again.")
            else:
                st.info("No contacts to save.")

elif st.session_state.current_page == 'property':
    st.markdown("<h1>Property Info</h1>", unsafe_allow_html=True)
    
    # Show current user and logout option
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.session_state.get('selected_user_name'):
            st.info(f"👤 Logged in as: {st.session_state['selected_user_name']}")
    with col2:
        if st.button("🚪 Logout", key="logout_property", type="secondary"):
            logout_user()
    
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
                    
                    # Format all property information using the same functions as DealFlow AI
                    physical_property = format_physical_property(result)
                    parcel_tax = format_parcel_tax_info(result)
                    ownership_sale = format_ownership_sale_info(result)
                    mortgage_lender = format_mortgage_lender_info(result)
                    
                    # Create consolidated Public Records field with same formatting
                    combined_public_records = f"𝗣𝗵𝘆𝘀𝗶𝗰𝗮𝗹 𝗣𝗿𝗼𝗽𝗲𝗿𝘁𝘆: \n{physical_property}\n\n𝗢𝘄𝗻𝗲𝗿𝘀𝗵𝗶𝗽 & 𝗦𝗮𝗹𝗲: \n{ownership_sale}\n\n𝗣𝗮𝗿𝗰𝗲𝗹 & 𝗧𝗮𝘅: \n{parcel_tax}\n\n𝗠𝗼𝗿𝘁𝗴𝗮𝗴𝗲 & 𝗟𝗲𝗻𝗱𝗲𝗿: \n{mortgage_lender}"
                    
                    # Display consolidated information
                    st.markdown("### Property Information")
                    st.text_area("Public Records", value=combined_public_records, height=1200)
                    
                else:
                    st.error("Could not validate this address. Please check the format and try again.")
        else:
            st.error("Please enter a property address.")
