import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation App", layout="wide")
st.title("📊 GI Reconciliation App (Export Button on Top)")

# Hardcoded example data for testing
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

# Metrics
st.metric("✅ Total Matched Rows", len(matched))
st.metric("⚠️ Total Unmatched Rows", len(unmatched))

# EXPORT BUTTON AT TOP
st.divider()
st.subheader("📥 Export All Results")

output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
output.seek(0)

st.download_button(
    label="📥 Download Excel File (Matched + Unmatched)",
    data=output,
    file_name="reconciliation_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# DataTables
st.divider()
st.subheader("✅ Matched Summary")
st.dataframe(matched)

st.subheader("⚠️ Unmatched Summary")
st.dataframe(unmatched)