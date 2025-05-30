import streamlit as st
import requests
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Airtable API setup
AIRTABLE_BASE_ID = "your_base_id"
AIRTABLE_TABLE_NAME = "Contacts"
AIRTABLE_API_KEY = "your_private_airtable_api_key"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

# FastAPI for backend functionality
from fastapi import FastAPI

app = FastAPI()

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

    response = requests.post(AIRTABLE_URL, headers=headers, json=payload)

    if response.status_code == 201:
        return JSONResponse(content={"status": "success", "message": "Contact saved to Airtable"}, status_code=200)
    else:
        return JSONResponse(content={"status": "error", "message": "Failed to save contact"}, status_code=400)

# Streamlit UI
def run_streamlit_app():
    st.title("Airtable Contact Manager")

    name = st.text_input("Name")
    email = st.text_input("Email")

    if st.button("Save Contact"):
        if name and email:
            response = requests.post(
                "http://localhost:8000/save-contact",
                json={"name": name, "email": email}
            )
            if response.status_code == 200:
                st.success("Contact saved successfully!")
            else:
                st.error("Failed to save contact.")
        else:
            st.error("Please fill out both fields.")

# Running Streamlit app
if __name__ == "__main__":
    run_streamlit_app()
