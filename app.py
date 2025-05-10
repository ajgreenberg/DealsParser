import streamlit as st
import json
import boto3
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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

def load_corrections():
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        return json.loads(obj["Body"].read())
    except Exception as e:
        st.error(f"Failed to load corrections: {e}")
        return {}

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

def display_human_readable(corrections: dict):
    st.markdown("### 🧠 Existing Correction Rules (Natural Format)")
    if not corrections:
        st.info("No rules yet.")
        return
    for key, val in corrections.items():
        if isinstance(val, dict):
            for wrong, correct in val.items():
                st.markdown(f"🔁 **Replace** `{wrong}` → `{correct}` in **{key}**")
        elif isinstance(val, list):
            for phrase in val:
                st.markdown(f"🚫 **Ignore phrases** like `{phrase}` in **{key}**" if key != "Ignore Phrases" else f"🚫 Ignore if text contains: `{phrase}`")

def interpret_feedback(feedback: str, existing: dict):
    prompt = f"""You are a helpful assistant. Given the user's feedback below, identify and return one or more correction rules in JSON format. Possible rule types include:
- A field substitution (e.g. replace 'Manufactured Housing Community' → 'Mobile Home Community' in 'Asset Class')
- A phrase to ignore
- A field-specific override (e.g. treat 'N/A' in 'Cap Rate' as null)

Return a minimal JSON that matches the structure of this existing rules dictionary:
{json.dumps(existing, indent=2)}

User feedback:
""" + feedback + "

Return ONLY valid JSON corrections:"
    res = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    try:
        content = res.choices[0].message.content
        new_rules = json.loads(content)
        return new_rules
    except Exception as e:
        st.error(f"Could not parse corrections: {e}")
        st.code(content)
        return {}

st.title("🧠 AI Feedback + Rule Learning")

corrections = load_corrections()
display_human_readable(corrections)

st.markdown("---")
st.subheader("💬 Add New Feedback")
feedback = st.text_area("Write your correction ideas in natural language (e.g. 'Don't call it Manufactured Housing')")

if st.button("🧠 Process Feedback"):
    if feedback.strip():
        with st.spinner("Thinking..."):
            new = interpret_feedback(feedback, corrections)
            if new:
                for field, rule in new.items():
                    if isinstance(rule, dict):
                        corrections.setdefault(field, {}).update(rule)
                    elif isinstance(rule, list):
                        corrections.setdefault(field, [])
                        for item in rule:
                            if item not in corrections[field]:
                                corrections[field].append(item)
                save_corrections(corrections)
    else:
        st.warning("Please enter some feedback.")
