def load_file(file):
    if file is not None:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            return pd.read_excel(file)
    return None

import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation App", layout="wide")
st.title("📊 GI Reconciliation - 4-Way Summary Split")

def load_data(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        pass
if atlantis_file and gmi_file:
    pass
else:
    pass

st.sidebar.header("📄 Upload Files")
atlantis_file = st.sidebar.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.sidebar.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    pass
st.subheader("📥 Export All Sections to Excel")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    qty_match_only.to_excel(writer, sheet_name="Qty_Match_Only", index=False)
    fee_match_only.to_excel(writer, sheet_name="Fee_Match_Only", index=False)
    qty_only.to_excel(writer, sheet_name="Qty_Only", index=False)
    fee_only.to_excel(writer, sheet_name="Fee_Only", index=False)
    rate_only.to_excel(writer, sheet_name="Rate_Only", index=False)
    
st.download_button(
    label="📥 Download Excel File (All 5 Sections)",
    data=buffer.getvalue(),
    file_name="reconciliation_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
matched.to_excel(writer, sheet_name="Matched", index=False)
qty_match_only.to_excel(writer, sheet_name="Qty_Match_Only", index=False)
fee_match_only.to_excel(writer, sheet_name="Fee_Match_Only", index=False)
qty_only.to_excel(writer, sheet_name="Qty_Only", index=False)
fee_only.to_excel(writer, sheet_name="Fee_Only", index=False)
rate_comparison.to_excel(writer, sheet_name="Rate_Compare", index=False)
st.download_button(
label="📤 Download Full Reconciliation Excel",
data=buffer.getvalue(),
file_name="reconciliation_summary.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.download_button(
label="📤 Download Full Reconciliation Excel",
data=buffer.getvalue(),
file_name="reconciliation_summary.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.download_button(
label="📥 Download Excel File (All 5 Sections)",
data=buffer,
file_name="reconciliation_summary.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    qty_match_only.to_excel(writer, sheet_name="Qty_Match_Only", index=False)
    fee_match_only.to_excel(writer, sheet_name="Fee_Match_Only", index=False)
    qty_only.to_excel(writer, sheet_name="Qty_Only", index=False)
    fee_only.to_excel(writer, sheet_name="Fee_Only", index=False)
    rate_only.to_excel(writer, sheet_name="Rate_Only", index=False)
    
st.download_button(
    label="📥 Download Excel File (All 5 Sections)",
    data=buffer.getvalue(),
    file_name="reconciliation_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    
    matched.to_excel(writer, sheet_name="Matched", index=False)
    qty_match_only.to_excel(writer, sheet_name="Qty_Match_Only", index=False)
    fee_match_only.to_excel(writer, sheet_name="Fee_Match_Only", index=False)
    no_match.to_excel(writer, sheet_name="No_Match", index=False)
    
    rate_comparison[['CB', 'Date', 'Account', 'Rate_Atlantis', 'Rate_GMI', 'Rate_Diff']].to_excel(writer, sheet_name="Rate_Comparison", index=False)
    
    buffer.seek(0)
st.download_button(
label="📥 Download Excel File (All 4 Sections)",
data=buffer,
file_name="reconciliation_summary.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)