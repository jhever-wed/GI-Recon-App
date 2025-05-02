import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="CB Summary Export", layout="wide")
st.title("📊 CB Summary Reconciliation with Export")

# Simulate user's expected structure and style
st.sidebar.header("Filters")
selected_months = st.sidebar.multiselect("Select Month", ["2025-02"], default=["2025-02"])

# Dummy data consistent with user's style
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

st.subheader("✅ Matched Summary")
st.dataframe(matched)

st.subheader("⚠️ Unmatched Summary")
st.dataframe(unmatched)

# Export Button placed according to user's prior working layout
st.markdown("---")
st.subheader("📥 Export Summary")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
buffer.seek(0)

st.download_button(
    label="📥 Download Reconciliation Excel",
    data=buffer,
    file_name="cb_summary_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)