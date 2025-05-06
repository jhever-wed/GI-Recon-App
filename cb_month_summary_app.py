import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation App", layout="wide")
st.title("📊 GI Reconciliation - 4-Way Summary Split")

def load_data(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        return pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

st.sidebar.header("📄 Upload Files")
atlantis_file = st.sidebar.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.sidebar.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        df1 = df1[df1['RecordType'] == 'TP']

        df1 = df1.rename(columns={
            'ExchangeEBCode': 'CB',
            'TradeDate': 'Date',
            'Quantity': 'Qty',
            'GiveUpAmt': 'Fee',
            'ClearingAccount': 'Account'
        })

        df2 = df2.rename(columns={
            'TGIVF#': 'CB',
            'TEDATE': 'Date',
            'TQTY': 'Qty',
            'TFEE5': 'Fee',
            'Acct': 'Account'
        })

        df1['Date'] = pd.to_datetime(df1['Date'].astype(str), format='%Y%m%d', errors='coerce')
        df2['Date'] = pd.to_datetime(df2['Date'].astype(str), format='%Y%m%d', errors='coerce')

        required_df1_cols = ['CB', 'Date', 'Qty', 'Fee', 'Account']
        required_df2_cols = ['CB', 'Date', 'Qty', 'Fee', 'Account']
        missing1 = [col for col in required_df1_cols if col not in df1.columns]
        missing2 = [col for col in required_df2_cols if col not in df2.columns]

        if missing1:
            st.error(f"❌ Missing columns in Atlantis file: {missing1}")
        elif missing2:
            st.error(f"❌ Missing columns in GMI file: {missing2}")
        else:
            summary1 = df1.groupby(['CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()
            summary2 = df2.groupby(['CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()

            summary1['CB'] = summary1['CB'].astype(str).str.strip()
            summary2['CB'] = summary2['CB'].astype(str).str.strip()

            summary1 = summary1.rename(columns={'Qty': 'Qty_Atlantis', 'Fee': 'Fee_Atlantis'})
            summary2 = summary2.rename(columns={'Qty': 'Qty_GMI', 'Fee': 'Fee_GMI'})

            merged = pd.merge(summary1, summary2, on=['CB', 'Date', 'Account'], how='outer')

            for col in ['Qty_Atlantis', 'Fee_Atlantis', 'Qty_GMI', 'Fee_GMI']:
                merged[col] = merged[col].fillna(0)

            merged['Qty_Diff'] = merged['Qty_Atlantis'] - merged['Qty_GMI']
            merged['Fee_Diff'] = merged['Fee_Atlantis'] + merged['Fee_GMI']

            matched = merged[(merged['Qty_Diff'].round(2) == 0) & (merged['Fee_Diff'].round(2) == 0)]
            qty_match_only = merged[(merged['Qty_Diff'].round(2) == 0) & (merged['Fee_Diff'].round(2) != 0)]
            fee_match_only = merged[(merged['Qty_Diff'].round(2) != 0) & (merged['Fee_Diff'].round(2) == 0)]
            no_match = merged[(merged['Qty_Diff'].round(2) != 0) & (merged['Fee_Diff'].round(2) != 0)]

            st.success("✅ Reconciliation Completed!")

            st.header("✅ Full Matches (Qty + Fee)")
            st.dataframe(matched)

            st.header("🔍 Qty Match Only (Fee mismatch)")
            st.dataframe(qty_match_only)

            st.header("🔍 Fee Match Only (Qty mismatch)")
            st.dataframe(fee_match_only)

            st.header("⚠️ No Match (Qty + Fee mismatch)")
            st.dataframe(no_match)

            st.markdown("---")
            st.subheader("📥 Export All Sections to Excel")

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                matched.to_excel(writer, sheet_name="Matched", index=False)
                qty_match_only.to_excel(writer, sheet_name="Qty_Match_Only", index=False)
                fee_match_only.to_excel(writer, sheet_name="Fee_Match_Only", index=False)
                no_match.to_excel(writer, sheet_name="No_Match", index=False)
            buffer.seek(0)

            st.download_button(
                label="📥 Download Excel File (All 4 Sections)",
                data=buffer,
                file_name="reconciliation_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )