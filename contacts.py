import streamlit as st
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import uvicorn
from threading import Thread
import os

# Helper function to get config from environment variables (Railway) or Streamlit secrets (local)
def get_config(key: str, default: str = None):
    """Get configuration from environment variable or Streamlit secrets."""
    # Try environment variable first (for Railway/production)
    value = os.getenv(key)
    if value:
        return value
    # Fall back to Streamlit secrets (for local development)
    try:
        return st.secrets.get(key, default)
    except:
        return default

# Set up Airtable credentials securely using environment variables or Streamlit's Secrets
AIRTABLE_BASE_ID = get_config("AIRTABLE_BASE_ID")
AIRTABLE_API_KEY = get_config("AIRTABLE_API_KEY") or get_config("AIRTABLE_PAT")  # Support both keys
AIRTABLE_TABLE_NAME = "Contacts"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

# FastAPI app to handle the POST request to save contacts
app = FastAPI()

# Define Pydantic model for request data (contact name and email)
class Contact(BaseModel):
    name: str
    email: str

@app.post("/save-contact")
async def save_contact(contact: Contact):
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "Name": contact.name,
            "Email": contact.email
        }
    }

    # Send request to Airtable to save the contact
    response = requests.post(AIRTABLE_URL, headers=headers, json=payload)

    if response.status_code == 201:
        return JSONResponse(content={"status": "success", "message": "Contact saved to Airtable"}, status_code=200)
    else:
        return JSONResponse(content={"status": "error", "message": "Failed to save contact"}, status_code=400)

# Run FastAPI backend
def run_backend():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Start FastAPI backend and keep Streamlit running
def start_app():
    thread = Thread(target=run_backend)
    thread.start()

# Keep Streamlit running without UI
if __name__ == "__main__":
    start_app()
