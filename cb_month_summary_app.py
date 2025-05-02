import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="CB Month Summary", layout="wide")

st.title("📊 CB Month Summary Reconciliation")

# Placeholder data (replace with your actual logic)
matched = pd.DataFrame({
    'CB': ['101', '202'],
    'Date': ['2025-02-01', '2025-02-02'],
    'Qty_Atlantis': [150, 250],
    'Fee_Atlantis': [60.00, 90.00],
    'Qty_GMI': [150, 250],
    'Fee_GMI': [-60.00, -90.00],
    'Qty_Diff': [0, 0],
    'Fee_Diff': [0.00, 0.00]
})

unmatched = pd.DataFrame({
    'CB': ['303'],
    'Date': ['2025-02-03'],
    'Qty_Atlantis': [180],
    'Fee_Atlantis': [85.00],
    'Qty_GMI': [100],
    'Fee_GMI': [-40.00],
    'Qty_Diff': [80],
    'Fee_Diff': [45.00]
})

# Display tables
st.header("✅ Matched Summary")
st.dataframe(matched)

st.header("⚠️ Unmatched Summary")
st.dataframe(unmatched)

# Add download button using BytesIO + Excel writer
st.divider()
st.subheader("📥 Export Matched and Unmatched")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
buffer.seek(0)

st.download_button(
    label="📥 Download Excel File",
    data=buffer,
    file_name="cb_summary_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)