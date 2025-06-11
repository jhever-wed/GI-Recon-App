import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation Dashboard", layout="wide")
st.title("📊 GI Reconciliation Dashboard")

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file, low_memory=False)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

# Sidebar for uploads and month selection
st.sidebar.header("📄 Upload Files")
atlantis_file = st.sidebar.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file      = st.sidebar.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        # Normalize column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Filter Atlantis
        if 'recordtype' in df1.columns:
            df1 = df1[df1['recordtype'].str.lower() == 'tp']

        # Rename columns
        df1 = df1.rename(columns={
            'exchangeebcode': 'cb', 'tradedate': 'date',
            'quantity': 'qty', 'giveupamt': 'fee', 'clearingaccount': 'account'
        })
        df2 = df2.rename(columns={
            'tgivf#': 'cb', 'tedate': 'date',
            'tqty': 'qty', 'tfee5': 'fee', 'acct': 'account'
        })

        # Parse dates & numeric fields
        df1['date'] = pd.to_datetime(df1['date'], format='%Y%m%d', errors='coerce')
        df2['date'] = pd.to_datetime(df2['date'], format='%Y%m%d', errors='coerce')
        for col in ['qty', 'fee']:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        # Month selector
        df1['month'] = df1['date'].dt.to_period('M')
        df2['month'] = df2['date'].dt.to_period('M')
        months = sorted(set(df1['month'].dropna()).union(df2['month'].dropna()))
        if not months:
            st.error("No data available for month selection.")
            st.stop()
        month_strs = [m.strftime('%Y-%m') for m in months]
        selected_str = st.sidebar.selectbox("Select Month", month_strs)
        selected_month = pd.Period(selected_str, freq='M')

        # Filter by selected month
        df1 = df1[df1['month'] == selected_month]
        df2 = df2[df2['month'] == selected_month]

        # Summaries for CB Summary (Golden Copy)
        summary1 = df1.groupby(['cb', 'date', 'account'], dropna=False)[['qty', 'fee']].sum().reset_index()
        summary2 = df2.groupby(['cb', 'date', 'account'], dropna=False)[['qty', 'fee']].sum().reset_index()
        summary1 = summary1.rename(columns={'qty': 'qty_atlantis', 'fee': 'fee_atlantis'})
        summary2 = summary2.rename(columns={'qty': 'qty_gmi', 'fee': 'fee_gmi'})
        merged = pd.merge(summary1, summary2, on=['cb', 'date', 'account'], how='outer').fillna(0)
        merged['qty_diff'] = merged['qty_atlantis'] - merged['qty_gmi']
        merged['fee_diff'] = merged['fee_atlantis'] + merged['fee_gmi']

        # Prepare mismatches
        mismatches = merged[
            (merged['qty_diff'] != 0) |
            (merged['fee_diff'] != 0)
        ].copy()

        # Tabs for display
        tab1, tab2 = st.tabs(["CB Summary", "Mismatch Summary"])
        with tab1:
            st.header("✅ CB Summary")
            st.dataframe(merged)

        with tab2:
            st.header("🚫 Mismatch Summary by Account & Date")
            st.dataframe(mismatches)

        # Unified download button for both
        st.subheader("📥 Download Full Report")
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            merged.to_excel(writer, sheet_name="CB_Summary", index=False)
            mismatches.to_excel(writer, sheet_name="Mismatch_Summary", index=False)
        buf.seek(0)
        st.download_button(
            label="Download Full Report",
            data=buf.getvalue(),
            file_name=f"full_reconciliation_{selected_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ----- New Mismatch Summary Section -----
# Assuming 'merged' DataFrame from golden logic exists
try:
    mismatches = merged[
        (merged['Qty_Atlantis'] != merged['Qty_GMI']) |
        (merged['Fee_Atlantis'] != merged['Fee_GMI'])
    ].copy()
    st.header("🚫 Mismatch Summary by Account & Date")
    st.dataframe(mismatches)
    st.subheader("📥 Download Mismatch Excel")
    buf_mis = io.BytesIO()
    with pd.ExcelWriter(buf_mis, engine="openpyxl") as writer:
        mismatches.to_excel(writer, sheet_name='Mismatches', index=False)
    buf_mis.seek(0)
    st.download_button(
        label="Download Mismatch Excel",
        data=buf_mis.getvalue(),
        file_name="mismatch_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument-spreadsheetml.sheet"
    )
except NameError:
    st.error("Mismatch section requires the reconciliation logic to define 'merged'.")
