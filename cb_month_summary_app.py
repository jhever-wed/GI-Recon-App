import streamlit as st
import pandas as pd
from io import BytesIO

# Simulated Summary and Detail DataFrames
summary_df = pd.DataFrame({
    'CB': ['00364', '00478'],
    'Month': ['2024-02', '2024-02'],
    'Qty': [1000, 2000],
    'Amt': [1500.00, 3000.00]
})

detail_df = pd.DataFrame({
    'CB': ['00364', '00364', '00478'],
    'TradeDate': ['2024-02-01', '2024-02-02', '2024-02-03'],
    'Qty': [500, 500, 2000],
    'Amt': [750.00, 750.00, 3000.00]
})

# Display
st.subheader("Summary")
st.dataframe(summary_df)
st.subheader("Detail")
st.dataframe(detail_df)

# Export logic
output = BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    summary_df.to_excel(writer, index=False, sheet_name="Summary")
    detail_df.to_excel(writer, index=False, sheet_name="Detail")
st.download_button(
    label="📥 Download Excel Export",
    data=output.getvalue(),
    file_name="gi-recon-results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
