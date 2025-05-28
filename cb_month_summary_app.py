import streamlit as st
import pandas as pd

st.title("GI-Recon Simplified")

uploaded_file1 = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    try:
        df1 = pd.read_csv(uploaded_file1, encoding='ISO-8859-1')
    except:
        df1 = pd.read_excel(uploaded_file1)
    try:
        df2 = pd.read_csv(uploaded_file2, encoding='ISO-8859-1')
    except:
        df2 = pd.read_excel(uploaded_file2)

    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    df1 = df1[df1['RECORDTYPE'] == 'TP']
    df2 = df2[df2['TGIVIO'] == 'GI']

    df1['DATE'] = pd.to_datetime(df1['TRADEDATE'])
    df2['DATE'] = pd.to_datetime(df2['TEDATE'])

    df1['QTY'] = pd.to_numeric(df1['QUANTITY'], errors='coerce')
    df2['QTY'] = pd.to_numeric(df2['TQTY'], errors='coerce')

    df1['FEE'] = pd.to_numeric(df1['GIVEUPAMT'], errors='coerce')
    df2['FEE'] = pd.to_numeric(df2['TFEE5'], errors='coerce')

    df1['CB'] = df1['EXCHANGEEBCODE']
    df2['CB'] = df2['TGIVIF#']

    grouped1 = df1.groupby(['CB', 'DATE']).agg({'QTY': 'sum', 'FEE': 'sum'}).reset_index()
    grouped2 = df2.groupby(['CB', 'DATE']).agg({'QTY': 'sum', 'FEE': 'sum'}).reset_index()

    merged = pd.merge(grouped1, grouped2, on=['CB', 'DATE'], suffixes=('_ATLANTIS', '_GMI'), how='outer').fillna(0)
    merged['QTY_DIFF'] = merged['QTY_ATLANTIS'] - merged['QTY_GMI']
    merged['FEE_DIFF'] = merged['FEE_ATLANTIS'] + merged['FEE_GMI']

    summary = merged.groupby('CB').agg({
        'QTY_ATLANTIS': 'sum',
        'QTY_GMI': 'sum',
        'FEE_ATLANTIS': 'sum',
        'FEE_GMI': 'sum',
        'QTY_DIFF': 'sum',
        'FEE_DIFF': 'sum'
    }).reset_index()

    st.subheader("Section 1: Summary by CB")
    st.dataframe(summary)

    st.subheader("Section 2: Detail (Matches + Non-Matches)")
    st.dataframe(merged)
