
import streamlit as st
import pandas as pd

st.set_page_config(page_title="GI Reconciliation App", layout="wide")
st.title("📊 GI Reconciliation - Simplified Summary View")

def load_data(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        return pd.read_csv(file, encoding='ISO-8859-1', low_memory=False)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

st.sidebar.header("📄 Upload Files")
uploaded_file1 = st.sidebar.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
uploaded_file2 = st.sidebar.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if uploaded_file1 and uploaded_file2:
    df1 = load_data(uploaded_file1)
    df2 = load_data(uploaded_file2)

    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    df1 = df1[df1['RECORDTYPE'] == 'TP']
    df2 = df2[df2['TGIVIO'] == 'GI']

    df1 = df1.rename(columns={
        'EXCHANGEEBCODE': 'CB',
        'TRADEDATE': 'DATE',
        'QUANTITY': 'QTY',
        'GIVEUPAMT': 'FEE',
        'CLEARINGACCOUNT': 'ACCOUNT'
    })

    df2 = df2.rename(columns={
        'TGIVF#': 'CB',
        'TEDATE': 'DATE',
        'TQTY': 'QTY',
        'TFEE5': 'FEE',
        'ACCT': 'ACCOUNT'
    })

    df1['DATE'] = pd.to_datetime(df1['DATE'].astype(str), format='%Y%m%d', errors='coerce')
    df2['DATE'] = pd.to_datetime(df2['DATE'].astype(str), format='%Y%m%d', errors='coerce')

    df1['QTY'] = pd.to_numeric(df1['QTY'], errors='coerce')
    df1['FEE'] = pd.to_numeric(df1['FEE'], errors='coerce')
    df2['QTY'] = pd.to_numeric(df2['QTY'], errors='coerce')
    df2['FEE'] = pd.to_numeric(df2['FEE'], errors='coerce')

    months1 = df1['DATE'].dt.to_period('M').dropna().unique()
    months2 = df2['DATE'].dt.to_period('M').dropna().unique()
    all_months = sorted(set(months1).union(set(months2)))
    selected_month = st.sidebar.selectbox("📅 Select Month", all_months)

    df1 = df1[df1['DATE'].dt.to_period('M') == selected_month]
    df2 = df2[df2['DATE'].dt.to_period('M') == selected_month]

    summary1 = df1.groupby(['CB', 'DATE', 'ACCOUNT'], dropna=False)[['QTY', 'FEE']].sum().reset_index()
    summary2 = df2.groupby(['CB', 'DATE', 'ACCOUNT'], dropna=False)[['QTY', 'FEE']].sum().reset_index()

    summary1 = summary1.rename(columns={'QTY': 'QTY_ATLANTIS', 'FEE': 'FEE_ATLANTIS'})
    summary2 = summary2.rename(columns={'QTY': 'QTY_GMI', 'FEE': 'FEE_GMI'})

    merged = pd.merge(summary1, summary2, on=['CB', 'DATE', 'ACCOUNT'], how='outer')
    merged['QTY_ATLANTIS'] = merged['QTY_ATLANTIS'].fillna(0)
    merged['FEE_ATLANTIS'] = merged['FEE_ATLANTIS'].fillna(0)
    merged['QTY_GMI'] = merged['QTY_GMI'].fillna(0)
    merged['FEE_GMI'] = merged['FEE_GMI'].fillna(0)

    merged['QTY_DIFF'] = (merged['QTY_ATLANTIS'] - merged['QTY_GMI']).round(2)
    merged['FEE_DIFF'] = (merged['FEE_ATLANTIS'] + merged['FEE_GMI']).round(2)

    st.header("📊 Summary by CB")
    top_summary = merged.groupby('CB')[['QTY_ATLANTIS', 'FEE_ATLANTIS', 'QTY_GMI', 'FEE_GMI']].sum().reset_index()
    top_summary['QTY_DIFF'] = (top_summary['QTY_ATLANTIS'] - top_summary['QTY_GMI']).round(2)
    top_summary['FEE_DIFF'] = (top_summary['FEE_ATLANTIS'] + top_summary['FEE_GMI']).round(2)
    st.dataframe(top_summary)

    st.subheader("📄 Detail Rows Making Up the Summary")
    st.dataframe(merged)
