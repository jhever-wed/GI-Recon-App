import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="CB Summary Reconciliation", layout="wide")
st.title("📊 CB Summary Reconciliation - Split Unmatched")

# Example dummy data
data = pd.DataFrame({
    'CB': ['101', '202', '303', '404'],
    'Date': ['2025-02-01', '2025-02-02', '2025-02-03', '2025-02-04'],
    'Qty_Atlantis': [150, 250, 180, 300],
    'Fee_Atlantis': [60.00, 90.00, 85.00, 100.00],
    'Qty_GMI': [150, 200, 100, 275],
    'Fee_GMI': [-60.00, -90.00, -30.00, -100.00]
})

data['Qty_Diff'] = data['Qty_Atlantis'] - data['Qty_GMI']
data['Fee_Diff'] = data['Fee_Atlantis'] + data['Fee_GMI']

# 4-way split
matched = data[(data['Qty_Diff'].round(2) == 0) & (data['Fee_Diff'].round(2) == 0)]
qty_match_only = data[(data['Qty_Diff'].round(2) == 0) & (data['Fee_Diff'].round(2) != 0)]
fee_match_only = data[(data['Qty_Diff'].round(2) != 0) & (data['Fee_Diff'].round(2) == 0)]
no_match = data[(data['Qty_Diff'].round(2) != 0) & (data['Fee_Diff'].round(2) != 0)]

# Show summaries
st.header("✅ Full Match (Qty + Fee)")
st.dataframe(matched)

st.header("🔍 Qty Match Only (Fee mismatch)")
st.dataframe(qty_match_only)

st.header("🔍 Fee Match Only (Qty mismatch)")
st.dataframe(fee_match_only)

st.header("⚠️ No Match (Qty + Fee mismatch)")
st.dataframe(no_match)