
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("GI Reconciliation - Mismatches Only Summary")

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

def read_file(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if atlantis_file and gmi_file:
    df1 = read_file(atlantis_file)
    df2 = read_file(gmi_file)

    # Normalize column names
    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    # Rename columns
    df1 = df1.rename(columns={
        "ExchangeEBCode": "CB",
        "TradeDate": "Date",
        "TQTY": "Qty",
        "GiveUpAmt": "Fee",
        "ClearingAccount": "Account",
        "GiveUpRate": "Rate"
    })

    df2 = df2.rename(columns={
        "TGIVF#": "CB",
        "TEDATE": "Date",
        "TQTY": "Qty",
        "TFEE5": "Fee",
        "Acct": "Account"
    })

    # Ensure dates are consistent
    df1["Date"] = pd.to_datetime(df1["Date"])
    df2["Date"] = pd.to_datetime(df2["Date"])

    # Summarize both
    summary1 = df1.groupby(['CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()
    summary2 = df2.groupby(['CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()

    summary1 = summary1.rename(columns={"Qty": "Qty_Atlantis", "Fee": "Fee_Atlantis"})
    summary2 = summary2.rename(columns={"Qty": "Qty_GMI", "Fee": "Fee_GMI"})

    # Merge and keep mismatches
    merged = pd.merge(summary1, summary2, on=['CB', 'Date', 'Account'], how='outer')

    mismatches = merged[
        (merged['Qty_Atlantis'] != merged['Qty_GMI']) |
        (merged['Fee_Atlantis'] != merged['Fee_GMI'])
    ].copy()

    # Fill NaNs
    mismatches[['Qty_Atlantis', 'Qty_GMI', 'Fee_Atlantis', 'Fee_GMI']] = mismatches[
        ['Qty_Atlantis', 'Qty_GMI', 'Fee_Atlantis', 'Fee_GMI']
    ].fillna(0)

    # Add diffs
    mismatches['Qty_Diff'] = mismatches['Qty_Atlantis'] - mismatches['Qty_GMI']
    mismatches['Fee_Diff'] = mismatches['Fee_Atlantis'] + mismatches['Fee_GMI']

    # Grouped summary
    summary_grouped = mismatches.groupby(['CB', 'Date', 'Account'], dropna=False)[
        ['Qty_GMI', 'Qty_Atlantis', 'Fee_GMI', 'Fee_Atlantis']
    ].sum().reset_index()

    st.subheader("📊 Mismatches Grouped by Account and Date")
    st.dataframe(summary_grouped)

    # Export button
    st.subheader("📥 Export Mismatch Summary")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_grouped.to_excel(writer, sheet_name="Mismatch_Summary", index=False)
        mismatches.to_excel(writer, sheet_name="Detailed_Mismatches", index=False)
    st.download_button("Download Excel", buffer.getvalue(), file_name="gi_mismatch_summary.xlsx")
