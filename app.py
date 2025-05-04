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
    
    st.code(json.dumps(payload, indent=2), language="json")
    st.write("POST", url)
    
    res = requests.post(url, headers=headers, json=payload)
    st.write("Response status code:", res.status_code)
    st.text(res.text)
    
    if res.status_code not in [200, 201]:
        st.error(f"Airtable error: {res.text}")
    else:
        st.success("✅ Deal saved to Airtable!")
