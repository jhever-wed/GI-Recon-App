import streamlit as st
import pandas as pd
import io
import datetime

st.set_page_config(page_title="GI Reconciliation App", layout="wide")
st.title("📊 GI Reconciliation App")

def load_data(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        return pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        return None

st.header("📄 Upload Files")
st.divider()

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        st.success("✅ Files loaded successfully!")

        df1 = df1[df1['RecordType'] == 'TP']

        df1 = df1.rename(columns={
            'ExchangeEBCode': 'CB',
            'TradeDate': 'Date',
            'Quantity': 'Qty',
            'GiveUpAmt': 'Fee'
        })
        df2 = df2.rename(columns={
            'TGIVF#': 'CB',
            'TEDATE': 'Date',
            'TQTY': 'Qty',
            'TFEE5': 'Fee'
        })

        df1['Date'] = pd.to_datetime(df1['Date'].astype(str), format='%Y%m%d', errors='coerce')
        df2['Date'] = pd.to_datetime(df2['Date'].astype(str), format='%Y%m%d', errors='coerce')

        df1['Month'] = df1['Date'].dt.to_period('M').astype(str)
        df2['Month'] = df2['Date'].dt.to_period('M').astype(str)

        common_months = sorted(set(df1['Month']) & set(df2['Month']))
        selected_months = st.multiselect(
            "📅 Select Month(s) to Reconcile",
            options=common_months,
            default=common_months
        )

        df1 = df1[df1['Month'].isin(selected_months)]
        df2 = df2[df2['Month'].isin(selected_months)]

        summary1 = df1.groupby(['CB', 'Date'], dropna=False)[['Qty', 'Fee']].sum().reset_index()
        summary2 = df2.groupby(['CB', 'Date'], dropna=False)[['Qty', 'Fee']].sum().reset_index()

        summary1["CB"] = summary1["CB"].astype(str).str.strip()
        summary2["CB"] = summary2["CB"].astype(str).str.strip()

        summary1 = summary1.rename(columns={'Qty': 'Qty_Atlantis', 'Fee': 'Fee_Atlantis'})
        summary2 = summary2.rename(columns={'Qty': 'Qty_GMI', 'Fee': 'Fee_GMI'})

        merged = pd.merge(summary1, summary2, on=['CB', 'Date'], how='outer')

        merged['Qty_Atlantis'] = merged['Qty_Atlantis'].fillna(0)
        merged['Qty_GMI'] = merged['Qty_GMI'].fillna(0)
        merged['Fee_Atlantis'] = merged['Fee_Atlantis'].fillna(0)
        merged['Fee_GMI'] = merged['Fee_GMI'].fillna(0)

        merged['Qty_Diff'] = merged['Qty_Atlantis'] - merged['Qty_GMI']
        merged['Fee_Diff'] = merged['Fee_Atlantis'] + merged['Fee_GMI']

        matched = merged[(merged['Qty_Diff'].round(2) == 0) & (merged['Fee_Diff'].round(2) == 0)]
        unmatched = merged[(merged['Qty_Diff'].round(2) != 0) | (merged['Fee_Diff'].round(2) != 0)]

        st.divider()
        st.header("📊 Summary")
        st.metric("✅ Total Matched Rows", len(matched))
        st.metric("⚠️ Total Unmatched Rows", len(unmatched))

        st.divider()
        st.subheader("✅ Matched Summary")
        st.dataframe(matched)

        st.divider()
        st.subheader("⚠️ Unmatched Summary")
        st.dataframe(unmatched)

        st.divider()
        st.subheader("📥 Download Report")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            matched.to_excel(writer, sheet_name="Matched", index=False)
            unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Export to Excel (Matched + Unmatched)",
            data=buffer,
            file_name="reconciliation_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )