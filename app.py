import streamlit as st
import json
import boto3

# --- S3 Setup ---
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
S3_BUCKET = "my-deal-attachments"
S3_REGION = "us-east-1"
S3_KEY = "customizations/customizations.json"

s3 = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# --- Load corrections from S3 ---
@st.cache_data(show_spinner=False)
def load_corrections():
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(obj["Body"].read())
    except Exception as e:
        st.error(f"Failed to load corrections: {e}")
        return {}

# --- Save corrections back to S3 ---
def save_corrections(corrections: dict):
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=S3_KEY,
            Body=json.dumps(corrections, indent=2).encode("utf-8"),
            ContentType="application/json"
        )
        st.success("✅ Corrections saved to S3.")
    except Exception as e:
        st.error(f"Failed to save corrections: {e}")

# --- Streamlit UI ---
st.title("✏️ AI Correction Rules")

corrections = load_corrections()
tab1, tab2 = st.tabs(["🔍 View/Edit Rules", "➕ Add New Rule"])

with tab1:
    st.subheader("Current Correction Rules")
    st.json(corrections)

with tab2:
    st.subheader("Add a New Replacement Rule")
    field = st.text_input("Field (e.g., Asset Class)")
    wrong = st.text_input("Incorrect Value (e.g., Manufactured Housing Community)")
    correct = st.text_input("Preferred Value (e.g., Mobile Home Community)")

    if st.button("➕ Add Rule"):
        if field and wrong and correct:
            if field not in corrections:
                corrections[field] = {}
            corrections[field][wrong] = correct
            save_corrections(corrections)
        else:
            st.warning("Please fill in all fields.")
