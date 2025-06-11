import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation Dashboard", layout="wide")
st.title("📊 GI Reconciliation – CB Summary & Mismatch Summary")

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file, low_memory=False)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

st.sidebar.header("📄 Upload Files")
atlantis_file = st.sidebar.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file      = st.sidebar.file_uploader("Upload GMI File",     type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        # Normalize and clean
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()
        df1 = df1[df1.get('recordtype','').str.lower() == 'tp']

        # Rename columns
        df1 = df1.rename(columns={
            'exchangeebcode':'cb','tradedate':'date',
            'quantity':'qty','giveupamt':'fee','clearingaccount':'account'
        })
        df2 = df2.rename(columns={
            'tgivf#':'cb','tedate':'date',
            'tqty':'qty','tfee5':'fee','acct':'account'
        })

        # Parse dates & numeric
        df1['date'] = pd.to_datetime(df1['date'], format='%Y%m%d', errors='coerce')
        df2['date'] = pd.to_datetime(df2['date'], format='%Y%m%d', errors='coerce')
        for col in ['qty','fee']:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        # Summaries for golden CB summary
        summary1 = df1.groupby(['cb','date','account'], dropna=False)[['qty','fee']].sum().reset_index()
        summary2 = df2.groupby(['cb','date','account'], dropna=False)[['qty','fee']].sum().reset_index()
        summary1 = summary1.rename(columns={'qty':'qty_atlantis','fee':'fee_atlantis'})
        summary2 = summary2.rename(columns={'qty':'qty_gmi','fee':'fee_gmi'})
        merged = pd.merge(summary1, summary2, on=['cb','date','account'], how='outer').fillna(0)

        # Tabs
        tab1, tab2 = st.tabs(["CB Summary","Mismatch Summary"])
        with tab1:
            st.header("✅ CB Summary")
            st.dataframe(merged)
        with tab2:
            mismatches = merged[
                (merged['qty_atlantis'] != merged['qty_gmi']) |
                (merged['fee_atlantis'] != merged['fee_gmi'])
            ]
            st.header("🚫 Mismatch Summary by Account & Date")
            st.dataframe(mismatches)

        # Unified download button
        st.subheader("📥 Download Full Report")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            merged.to_excel(writer, sheet_name="CB_Summary", index=False)
            mismatches.to_excel(writer, sheet_name="Mismatch_Summary", index=False)
        buf.seek(0)
        st.download_button(
            label="Download Full Report",
            data=buf.getvalue(),
            file_name="full_reconciliation_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
