import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation – Golden CB & Mismatch", layout="wide")
st.title("📊 GI Reconciliation – CB Summary & Mismatch")

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
        # Standardize and filter
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        df1 = df1[df1['RecordType'] == 'TP']

        # Rename to unified names
        df1 = df1.rename(columns={
            'ExchangeEBCode':'CB','TradeDate':'Date',
            'Quantity':'Qty','GiveUpAmt':'Fee','ClearingAccount':'Account'
        })
        df2 = df2.rename(columns={
            'TGIVF#':'CB','TEDATE':'Date',
            'TQTY':'Qty','TFEE5':'Fee','Acct':'Account'
        })

        # Parse dates & numeric
        df1['Date'] = pd.to_datetime(df1['Date'].astype(str), format='%Y%m%d', errors='coerce')
        df2['Date'] = pd.to_datetime(df2['Date'].astype(str), format='%Y%m%d', errors='coerce')
        for col in ['Qty','Fee']:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        # Create merged summary
        summary1 = df1.groupby(['CB','Date','Account'], dropna=False)[['Qty','Fee']].sum().reset_index().rename(
            columns={'Qty':'Qty_Atlantis','Fee':'Fee_Atlantis'})
        summary2 = df2.groupby(['CB','Date','Account'], dropna=False)[['Qty','Fee']].sum().reset_index().rename(
            columns={'Qty':'Qty_GMI','Fee':'Fee_GMI'})
        merged = pd.merge(summary1, summary2, on=['CB','Date','Account'], how='outer').fillna(0)
        merged['Qty_Diff'] = merged['Qty_Atlantis'] - merged['Qty_GMI']
        merged['Fee_Diff'] = merged['Fee_Atlantis'] + merged['Fee_GMI']

        # Show CB summary
        st.header("✅ CB Summary (Full Merged)")
        st.dataframe(merged)

        # Show mismatches
        mismatches = merged[(merged['Qty_Diff'] != 0) | (merged['Fee_Diff'] != 0)]
        st.header("🚫 Mismatch Summary by Account & Date")
        st.dataframe(mismatches)

        # Export both
        st.subheader("📥 Download Full Report")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            merged.to_excel(writer, sheet_name='CB_Summary', index=False)
            mismatches.to_excel(writer, sheet_name='Mismatch_Summary', index=False)
        buf.seek(0)
        st.download_button(
            label="Download Full Report",
            data=buf.getvalue(),
            file_name="full_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
