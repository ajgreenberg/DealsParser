import requests
from bs4 import BeautifulSoup
import streamlit as st
import json
import time
import re

# Airtable secrets
AIRTABLE_PAT = st.secrets["AIRTABLE_PAT"]
AIRTABLE_BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = st.secrets["AIRTABLE_TABLE_NAME"]

def save_to_airtable(fields: dict):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={"fields": fields})
    if response.status_code != 200:
        st.error(f"❌ Airtable error: {response.text}")
    return response.status_code

def extract_square_footage(text):
    match = re.search(r"([\d,]+)\s*(SF|Sq Ft|square feet)", text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return 0

def scrape_crexi_with_pdf_filter():
    headers = {"User-Agent": "Mozilla/5.0"}
    search_url = "https://www.crexi.com/properties?property_type=industrial&transaction_type=sale&sort=-relevance"
    page = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    cards = soup.find_all("a", class_="styles_propertyCard__2g4Wb", href=True)
    scraped = 0

    for card in cards:
        try:
            detail_path = card['href']
            detail_url = "https://www.crexi.com" + detail_path
            detail_page = requests.get(detail_url, headers=headers)
            detail_soup = BeautifulSoup(detail_page.content, "html.parser")

            title = detail_soup.find("h1").text.strip()
            location = detail_soup.find("span", class_="styles_location__QG_Op").text.strip()

            description_text = detail_soup.get_text()
            square_footage = extract_square_footage(description_text)

            if square_footage < 45000:
                continue

            price_tag = detail_soup.find(string=re.compile(r"\$[\d,.]+"))
            price_text = price_tag.strip() if price_tag else "N/A"

            # Try to find OM PDF download link
            om_link_tag = detail_soup.find("a", href=re.compile(r".*\.pdf"))
            om_pdf_url = "https://www.crexi.com" + om_link_tag["href"] if om_link_tag else None
            

            fields = {
                "Property Name": title,
                "Location": location,
                "Asking Price": price_text,
                "Asset Class": "Industrial",
                "Cap Rate": "N/A",
                "Size": f"{square_footage:,} SF",
                "Key Highlights": "Scraped from Crexi. Industrial. Over 45,000 SF.",
                "Risks": "Unverified. Manual diligence required.",
                "Summary": f"{title} in {location}. Asking: {price_text}. Size: {square_footage:,} SF.",
                "URL": detail_url,
                "OM PDF": attachments
            }

            code = save_to_airtable(fields)
            if code == 200:
                scraped += 1
                time.sleep(1)

        except Exception as e:
            st.warning(f"Error processing listing: {e}")

    return scraped

# Streamlit UI
st.title("🏗️ Enhanced Crexi Scraper: Industrial 45k+ SF with OM PDFs")

if st.button("Scrape & Upload Listings"):
    with st.spinner("Scraping Crexi..."):
        count = scrape_crexi_with_pdf_filter()
    st.success(f"✅ {count} listings uploaded to Airtable.")
