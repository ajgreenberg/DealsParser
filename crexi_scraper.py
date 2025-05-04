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

def scrape_crexi_basic():
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

            price_tag = detail_soup.find(string=re.compile(r"\$[\d,.]+"))
            price_text = price_tag.strip() if price_tag else "N/A"

            fields = {
                "Property Name": title,
                "Location": location,
                "Asking Price": price_text,
                "Asset Class": "Industrial",
                "Cap Rate": "N/A",
                "Size": "N/A",
                "Key Highlights": "Scraped from Crexi.",
                "Risks": "Unverified. Manual diligence required.",
                "Summary": f"{title} in {location}. Asking: {price_text}.",
                "URL": detail_url
            }

            st.write(f"✅ Uploading: {title} | {location} | {price_text}")
            code = save_to_airtable(fields)
            if code == 200:
                scraped += 1
                time.sleep(1)

        except Exception as e:
            st.warning(f"Error processing listing: {e}")

    return scraped

# Streamlit UI
st.title("🏗️ Crexi Scraper: Industrial Deals (No SF Filter)")

if st.button("Scrape Listings"):
    with st.spinner("Scraping Crexi..."):
        count = scrape_crexi_basic()
    st.success(f"✅ {count} listings uploaded to Airtable.")
