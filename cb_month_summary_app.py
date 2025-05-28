
import streamlit as st
import pandas as pd

st.title("GI-Recon Simplified")

# Dummy logic for simplified 2-section layout
uploaded_file1 = st.file_uploader("Upload Atlantis File")
uploaded_file2 = st.file_uploader("Upload GMI File")

if uploaded_file1 and uploaded_file2:
    df1 = pd.read_csv(uploaded_file1, encoding='ISO-8859-1')
    df2 = pd.read_csv(uploaded_file2, encoding='ISO-8859-1')

    # Simple summaries for testing
    df1['Qty'] = pd.to_numeric(df1['Qty'], errors='coerce')
    df2['TQTY'] = pd.to_numeric(df2['TQTY'], errors='coerce')
    df1['TradeDate'] = pd.to_datetime(df1['TradeDate'], errors='coerce')
    df2['TEDATE'] = pd.to_datetime(df2['TEDATE'], errors='coerce')

    summary = df1.groupby(['ExchangeEBCode', df1['TradeDate'].dt.month])['Qty'].sum().reset_index()
    st.subheader("Section 1: Summary")
    st.dataframe(summary)

    st.subheader("Section 2: Details")
    st.dataframe(df1)
