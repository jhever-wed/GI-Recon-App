import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation – Mismatch Summary", layout="wide")
st.title("🚫 GI Reconciliation – Mismatch Summary")

def load_data(file):
    ext = file.name.split('.')[-1]
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
        # Normalize and filter
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        df1 = df1[df1['RecordType']=='TP']

        # Rename columns
        df1 = df1.rename(columns={
            'ExchangeEBCode':'CB','TradeDate':'Date',
            'Quantity':'Qty','GiveUpAmt':'Fee','ClearingAccount':'Account'
        }))
        df2 = df2.rename(columns={
            'TGIVF#':'CB','TEDATE':'Date',
            'TQTY':'Qty','TFEE5':'Fee','Acct':'Account'
        }))

        # Parse dates and numeric
        df1['Date'] = pd.to_datetime(df1['Date'], format='%Y%m%d', errors='coerce')
        df2['Date'] = pd.to_datetime(df2['Date'], format='%Y%m%d', errors='coerce')
        for col in ['Qty','Fee']:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        # Summaries
        s1 = df1.groupby(['CB','Date','Account'], dropna=False)[['Qty','Fee']].sum().reset_index()
        s1 = s1.rename(columns={'Qty':'Qty_Atlantis','Fee':'Fee_Atlantis'}))
        s2 = df2.groupby(['CB','Date','Account'], dropna=False)[['Qty','Fee']].sum().reset_index()
        s2 = s2.rename(columns={'Qty':'Qty_GMI','Fee':'Fee_GMI'}))

        # Merge and filter mismatches
        merged = pd.merge(s1, s2, on=['CB','Date','Account'], how='outer')
        merged[['Qty_Atlantis','Fee_Atlantis','Qty_GMI','Fee_GMI']] = merged[['Qty_Atlantis','Fee_Atlantis','Qty_GMI','Fee_GMI']].fillna(0)
        mismatches = merged[
            (merged['Qty_Atlantis'] != merged['Qty_GMI']) |
            (merged['Fee_Atlantis'] != merged['Fee_GMI'])
        ].copy()

        st.success(f"✅ Found {{len(mismatches)}} mismatches")

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
            file_name="mismatch_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument-spreadsheetml.sheet"
        )
