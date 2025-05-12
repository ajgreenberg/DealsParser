# [Previous code remains unchanged up to the 'if "summary" in st.session_state:' line]

if "summary" in st.session_state:
    st.subheader("✏️ Review and Edit Deal Details")
    with st.form("edit_deal_form"):
        summary = st.session_state["summary"]
        property_name = st.text_input("Property Name", value=summary.get("Property Name", ""))
        location = st.text_input("Location", value=summary.get("Location", ""))
        asset_class = st.text_input("Asset Class", value=summary.get("Asset Class", ""))
        purchase_price = st.text_input("Purchase Price", value=summary.get("Purchase Price", ""))
        loan_amount = st.text_input("Loan Amount", value=summary.get("Loan Amount", ""))
        in_place_cap_rate = st.text_input("In-Place Cap Rate", value=summary.get("In-Place Cap Rate", ""))
        stabilized_cap_rate = st.text_input("Stabilized Cap Rate", value=summary.get("Stabilized Cap Rate", ""))
        interest_rate = st.text_input("Interest Rate", value=summary.get("Interest Rate", ""))
        term = st.text_input("Term", value=summary.get("Term", ""))
        exit_strategy = st.text_input("Exit Strategy", value=summary.get("Exit Strategy", ""))
        projected_irr = st.text_input("Projected IRR", value=summary.get("Projected IRR", ""))
        hold_period = st.text_input("Hold Period", value=summary.get("Hold Period", ""))
        size = st.text_input("Size (Square Footage or Unit Count)", value=summary.get("Square Footage or Unit Count", ""))
        key_highlights = st.text_area("Key Highlights (one per line)", value="\n".join(summary.get("Key Highlights", [])))
        risks = st.text_area("Risks or Red Flags (one per line)", value="\n".join(summary.get("Risks or Red Flags", [])))
        summary_text = st.text_area("Summary", value=summary.get("Summary", ""))
        feedback = st.text_area("Feedback (optional)", value=st.session_state.get("feedback", ""))
        submitted = st.form_submit_button("📤 Upload this deal to Airtable")

    if submitted:
        updated_summary = {
            "Property Name": property_name,
            "Location": location,
            "Asset Class": asset_class,
            "Purchase Price": purchase_price,
            "Loan Amount": loan_amount,
            "In-Place Cap Rate": in_place_cap_rate,
            "Stabilized Cap Rate": stabilized_cap_rate,
            "Interest Rate": interest_rate,
            "Term": term,
            "Exit Strategy": exit_strategy,
            "Projected IRR": projected_irr,
            "Hold Period": hold_period,
            "Square Footage or Unit Count": size,
            "Key Highlights": key_highlights.strip().split("\n"),
            "Risks or Red Flags": risks.strip().split("\n"),
            "Summary": summary_text
        }
        with st.spinner("Uploading..."):
            create_airtable_record(
                updated_summary,
                st.session_state["notes"],
                st.session_state["attachments"],
                st.session_state["deal_type"],
                st.session_state["contacts"],
                feedback
            )
        st.success("Deal uploaded to Airtable successfully!")
