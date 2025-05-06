
import streamlit as st
import pandas as pd
import io

# --- Sample DataFrames (placeholders) ---
matched = pd.DataFrame()
qty_match_only = pd.DataFrame()
fee_match_only = pd.DataFrame()
unmatched = pd.DataFrame()
rate_comparison = pd.DataFrame()

# --- UI Section ---
st.subheader("📥 Export All Sections to Excel")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    matched.to_excel(writer, sheet_name="Matched", index=False)
    qty_match_only.to_excel(writer, sheet_name="Qty_Match_Only", index=False)
    fee_match_only.to_excel(writer, sheet_name="Fee_Match_Only", index=False)
    unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
    rate_comparison.to_excel(writer, sheet_name="Rate_Comparison", index=False)

st.download_button(
    label="📥 Download Excel File (All 5 Sections)",
    data=buffer.getvalue(),
    file_name="gi_recon_all_5_sections.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
