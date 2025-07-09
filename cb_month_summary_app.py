import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation App", layout="wide")
st.title("📊 GI Reconciliation - 4-Way Summary Split")

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
gmi_file = st.sidebar.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)

# Select symbol column for Atlantis
symbol1 = st.selectbox('Select Atlantis symbol column', df1.columns.tolist())
df1['symbol'] = df1[symbol1]

    df2 = load_data(gmi_file)

# Select symbol column for GMI
symbol2 = st.selectbox('Select GMI symbol column', df2.columns.tolist())
df2['symbol'] = df2[symbol2]

    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()

    df1 = df1[df1['RecordType'] == 'TP']
    df2 = df2[df2['TGIVIO'] == 'GI']

    df1 = df1.rename(columns={
        'ExchangeEBCode': 'CB',
        'TradeDate': 'Date',
        'Quantity': 'Qty',
        'GiveUpAmt': 'Fee',
        'ClearingAccount': 'Account'
    })
    # Add symbol field from Atlantis
    df1['symbol'] = df1['PRODUCT']

    df2 = df2.rename(columns={
        'TGIVF#': 'CB',
        'TEDATE': 'Date',
        'TQTY': 'Qty',
        'TFEE5': 'Fee',
        'ACCT': 'Account'
    })
    # Add symbol field from GMI
    df2['symbol'] = df2['TFC']

    df1['Date'] = pd.to_datetime(df1['Date'].astype(str), format='%Y%m%d', errors='coerce')
    df2['Date'] = pd.to_datetime(df2['Date'].astype(str), format='%Y%m%d', errors='coerce')

    df1['Qty'] = pd.to_numeric(df1['Qty'], errors='coerce')
    df1['Fee'] = pd.to_numeric(df1['Fee'], errors='coerce')
    df2['Qty'] = pd.to_numeric(df2['Qty'], errors='coerce')
    df2['Fee'] = pd.to_numeric(df2['Fee'], errors='coerce')

    months1 = df1['Date'].dt.to_period('M').dropna().unique()
    months2 = df2['Date'].dt.to_period('M').dropna().unique()
    all_months = sorted(set(months1).union(set(months2)))
    selected_month = st.sidebar.selectbox("📅 Select Month", all_months)

    df1 = df1[df1['Date'].dt.to_period('M') == selected_month]
    df2 = df2[df2['Date'].dt.to_period('M') == selected_month]

    summary1 = df1.groupby(['symbol', 'CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()
    summary2 = df2.groupby(['symbol', 'CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()

    summary1['CB'] = summary1['CB'].astype(str).str.strip()
    summary2['CB'] = summary2['CB'].astype(str).str.strip()

    summary1 = summary1.rename(columns={'Qty': 'Qty_Atlantis', 'Fee': 'Fee_Atlantis'})
    summary2 = summary2.rename(columns={'Qty': 'Qty_GMI', 'Fee': 'Fee_GMI'})

    merged = pd.merge(summary1, summary2, on=['symbol', 'CB', 'Date', 'Account'], how='outer')

    st.header("📊 Summary by CB")
    top_summary = merged.groupby(['symbol', 'CB'])[['Qty_Atlantis', 'Fee_Atlantis', 'Qty_GMI', 'Fee_GMI']].sum().reset_index()
    top_summary['Qty_Diff'] = (top_summary['Qty_Atlantis'] - top_summary['Qty_GMI']).round(2)
    top_summary['Fee_Diff'] = (top_summary['Fee_Atlantis'] + top_summary['Fee_GMI']).round(2)
    st.dataframe(top_summary)

    for col in ['Qty_Atlantis', 'Fee_Atlantis', 'Qty_GMI', 'Fee_GMI']:
        merged[col] = merged[col].fillna(0)

    merged['Qty_Diff'] = (merged['Qty_Atlantis'] - merged['Qty_GMI']).round(2)
    merged['Fee_Diff'] = (merged['Fee_Atlantis'] + merged['Fee_GMI']).round(2)

    matched = merged[(merged['Qty_Diff'] == 0) & (merged['Fee_Diff'] == 0)]
    qty_match_only = merged[(merged['Qty_Diff'] == 0) & (merged['Fee_Diff'] != 0)]
    fee_match_only = merged[(merged['Qty_Diff'] != 0) & (merged['Fee_Diff'] == 0)]
    no_match = merged[(merged['Qty_Diff'] != 0) & (merged['Fee_Diff'] != 0)]

    st.success("✅ Reconciliation Completed!")

    st.header("✅ Full Matches (Qty + Fee)")
    st.dataframe(matched)

    st.header("🔍 Qty Match Only (Fee mismatch)")
    st.dataframe(qty_match_only)

    st.header("🔍 Fee Match Only (Qty mismatch)")
    st.dataframe(fee_match_only)

    st.header("⚠️ No Match (Qty + Fee mismatch)")
    st.dataframe(no_match)

    # Export Excel with top summary tab
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        top_summary = merged.groupby(['symbol', 'CB'])[['Qty_Atlantis', 'Fee_Atlantis', 'Qty_GMI', 'Fee_GMI']].sum().reset_index()
        top_summary['Qty_Diff'] = (top_summary['Qty_Atlantis'] - top_summary['Qty_GMI']).round(2)
        top_summary['Fee_Diff'] = (top_summary['Fee_Atlantis'] + top_summary['Fee_GMI']).round(2)
        top_summary.to_excel(writer, sheet_name='Top Summary by CB', index=False)
        matched.to_excel(writer, sheet_name='Full Matches', index=False)
        qty_match_only.to_excel(writer, sheet_name='Qty Match Only', index=False)
        fee_match_only.to_excel(writer, sheet_name='Fee Match Only', index=False)
        no_match.to_excel(writer, sheet_name='No Match', index=False)

    st.download_button(
        label="📥 Download Reconciliation Excel",
        data=output.getvalue(),
        file_name="reconciliation_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )