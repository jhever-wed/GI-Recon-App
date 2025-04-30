import streamlit as st
import pandas as pd
import io
import base64

st.set_page_config(page_title="GI Reconciliation App - HTML Link", layout="wide")
st.title("📊 GI Reconciliation App (Export via HTML Link)")

# Sample matched and unmatched data
matched = pd.DataFrame({
    'CB': ['100', '200'],
    'Date': ['2025-02-01', '2025-02-02'],
    'Qty_Atlantis': [100, 200],
    'Fee_Atlantis': [50.25, 75.00],
    'Qty_GMI': [100, 200],
    'Fee_GMI': [-50.25, -75.00],
    'Qty_Diff': [0, 0],
    'Fee_Diff': [0.0, 0.0]
})

unmatched = pd.DataFrame({
    'CB': ['300'],
    'Date': ['2025-02-03'],
    'Qty_Atlantis': [150],
    'Fee_Atlantis': [60.00],
    'Qty_GMI': [100],
    'Fee_GMI': [-30.00],
    'Qty_Diff': [50],
    'Fee_Diff': [30.00]
})

# Create Excel in memory
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
buffer.seek(0)

# Encode as base64 for download link
b64 = base64.b64encode(buffer.read()).decode()
href = f'<a href="data:application/octet-stream;base64,{b64}" download="reconciliation_summary.xlsx">📥 Click here to download Excel file</a>'

st.subheader("✅ Matched Summary")
st.dataframe(matched)

st.subheader("⚠️ Unmatched Summary")
st.dataframe(unmatched)

# Show HTML download link
st.divider()
st.markdown("### 📥 Export Summary File")
st.markdown(href, unsafe_allow_html=True)