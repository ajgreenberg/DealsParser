from fastapi import FastAPI, HTTPException
import requests
from pydantic import BaseModel

app = FastAPI()

# Airtable API setup
AIRTABLE_BASE_ID = "your_base_id"
AIRTABLE_TABLE_NAME = "Contacts"
AIRTABLE_API_KEY = "your_private_airtable_api_key"
AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"

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
        return {"status": "success", "message": "Contact saved to Airtable"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to save contact")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

