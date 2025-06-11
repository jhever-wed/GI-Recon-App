import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation – Mismatch Summary", layout="wide")
st.title("🚫 GI Reconciliation – Mismatch Summary")

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
gmi_file     = st.sidebar.file_uploader("Upload GMI File",     type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        # Normalize column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Filter Atlantis records
        df1 = df1[df1.get('recordtype', '') == 'TP']

        # Rename columns uniformly
        df1 = df1.rename(columns={
            'exchangeebcode':'cb','tradedate':'date',
            'quantity':'qty','giveupamt':'fee','clearingaccount':'account'
        })
        df2 = df2.rename(columns={
            'tgivf#':'cb','tedate':'date',
            'tqty':'qty','tfee5':'fee','acct':'account'
        })

        # Parse dates and numeric fields
        df1['date'] = pd.to_datetime(df1['date'], format='%Y%m%d', errors='coerce')
        df2['date'] = pd.to_datetime(df2['date'], format='%Y%m%d', errors='coerce')
        for col in ['qty','fee']:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        # Month selector
        df1['month'] = df1['date'].dt.to_period('M')
        df2['month'] = df2['date'].dt.to_period('M')
        months = sorted(df1['month'].dropna().unique())
        selected_month = st.sidebar.selectbox("Select Month", months, format_func=lambda x: x.strftime("%Y-%m"))
        df1 = df1[df1['month'] == selected_month]
        df2 = df2[df2['month'] == selected_month]

        # Summaries
        s1 = df1.groupby(['cb','date','account'], dropna=False)[['qty','fee']].sum().reset_index()
        s1 = s1.rename(columns={'qty':'qty_atlantis','fee':'fee_atlantis'})
        s2 = df2.groupby(['cb','date','account'], dropna=False)[['qty','fee']].sum().reset_index()
        s2 = s2.rename(columns={'qty':'qty_gmi','fee':'fee_gmi'})

        # Merge and filter mismatches
        merged = pd.merge(s1, s2, on=['cb','date','account'], how='outer')
        merged[['qty_atlantis','fee_atlantis','qty_gmi','fee_gmi']] = merged[['qty_atlantis','fee_atlantis','qty_gmi','fee_gmi']].fillna(0)
        mismatches = merged[
            (merged['qty_atlantis'] != merged['qty_gmi']) |
            (merged['fee_atlantis'] != merged['fee_gmi'])
        ].copy()

        st.success(f"✅ Found {len(mismatches)} mismatches for {selected_month.strftime('%Y-%m')}")

        st.header("📊 Mismatch Summary by Account & Date")
        st.dataframe(mismatches)

        # Export mismatches
        st.subheader("📥 Download Mismatch Excel")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            mismatches.to_excel(writer, sheet_name='Mismatches', index=False)
        buf.seek(0)
        st.download_button(
            label="Download Mismatch Excel",
            data=buf.getvalue(),
            file_name=f"mismatch_summary_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
