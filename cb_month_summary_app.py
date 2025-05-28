
import streamlit as st
import pandas as pd

st.title("GI Recon - Validated Preview")

uploaded_file1 = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    try:
        df1 = pd.read_csv(uploaded_file1, encoding='ISO-8859-1', low_memory=False)
    except:
        df1 = pd.read_excel(uploaded_file1)

    try:
        df2 = pd.read_csv(uploaded_file2, encoding='ISO-8859-1', low_memory=False)
    except:
        df2 = pd.read_excel(uploaded_file2)

    df1['Qty'] = pd.to_numeric(df1.get('Qty', 0), errors='coerce')
    df1['Amt'] = pd.to_numeric(df1.get('Amt', 0), errors='coerce')
    df2['Qty'] = pd.to_numeric(df2.get('Qty', 0), errors='coerce')
    df2['Amt'] = pd.to_numeric(df2.get('Amt', 0), errors='coerce')

    combined = pd.concat([df1, df2], ignore_index=True)
    summary = combined.groupby('CB')[['Qty', 'Amt']].sum().reset_index()

    st.subheader("Summary")
    st.dataframe(summary)

    st.subheader("Detail")
    st.dataframe(combined)
