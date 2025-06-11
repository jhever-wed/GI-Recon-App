import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation Dashboard", layout="wide")
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
atlantis_file = st.sidebar.file_uploader("Upload Atlantis File",      type=["csv", "xls", "xlsx"])
gmi_file      = st.sidebar.file_uploader("Upload GMI File",           type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)
    if df1 is not None and df2 is not None:
        # Normalize columns to lowercase for mapping
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Filter Atlantis TP records
        if 'recordtype' in df1.columns:
            df1 = df1[df1['recordtype'].str.lower() == 'tp']

        # Rename Atlantis columns to standardized uppercase
        df1 = df1.rename(columns={
            'exchangeebcode':'CB',
            'tradedate':'Date',
            'quantity':'Qty',
            'giveupamt':'Fee',
            'clearingaccount':'Account'
        })

        # Build mapping for GMI columns
        col_map = {col:col for col in df2.columns}
        rename_gmi = {}
        # Map known keys to uppercase names
        for lower, upper in [('tgivf#','CB'),('tedate','Date'),('tqty','Qty'),('tfee5','Fee')]:
            if lower in col_map:
                rename_gmi[col_map[lower]] = upper
        # Account mapping
        if 'acct' in col_map:
            rename_gmi[col_map['acct']] = 'Account'
        elif 'account' in col_map:
            rename_gmi[col_map['account']] = 'Account'
        else:
            st.error("Missing 'Acct' (or 'Account') column in GMI file")
            st.stop()

        df2 = df2.rename(columns=rename_gmi)

        # Parse dates and numeric fields
        df1['Date'] = pd.to_datetime(df1['Date'], format='%Y%m%d', errors='coerce')
        df2['Date'] = pd.to_datetime(df2['Date'], format='%Y%m%d', errors='coerce')
        for col in ['Qty','Fee']:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        # Generate summaries
        summary1 = df1.groupby(['CB','Date','Account'], dropna=False)[['Qty','Fee']].sum().reset_index()
        summary1 = summary1.rename(columns={'Qty':'Qty_Atlantis','Fee':'Fee_Atlantis'})
        summary2 = df2.groupby(['CB','Date','Account'], dropna=False)[['Qty','Fee']].sum().reset_index()
        summary2 = summary2.rename(columns={'Qty':'Qty_GMI','Fee':'Fee_GMI'})

        # Merge, fillna, and compute diffs
        merged = pd.merge(summary1, summary2, on=['CB','Date','Account'], how='outer')
        for c in ['Qty_Atlantis','Fee_Atlantis','Qty_GMI','Fee_GMI']:
            merged[c] = merged[c].fillna(0)
        merged['Qty_Diff'] = merged['Qty_Atlantis'] - merged['Qty_GMI']
        merged['Fee_Diff'] = merged['Fee_Atlantis'] + merged['Fee_GMI']

        # Display CB Summary
        st.header("✅ CB Summary")
        st.dataframe(merged)

        # Display mismatches
        mismatches = merged[(merged['Qty_Diff'] != 0) | (merged['Fee_Diff'] != 0)]
        st.header("🚫 Mismatch Summary by Account & Date")
        st.dataframe(mismatches)

        # Download both sheets
        st.subheader("📥 Download Full Report")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            merged.to_excel(writer, sheet_name='CB_Summary', index=False)
            mismatches.to_excel(writer, sheet_name='Mismatch_Summary', index=False)
        buf.seek(0)
        st.download_button("Download Full Report", buf.getvalue(),
                           file_name="full_reconciliation_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
