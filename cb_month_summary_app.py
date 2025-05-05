
import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

def load_data(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        return pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

st.title("GI Reconciliation App (CB + Date + Account Match)")

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
        st.write('Atlantis columns:', df1.columns.tolist())
    df2 = load_data(gmi_file)
        st.write('GMI columns:', df2.columns.tolist())

    if df1 is not None and df2 is not None:
        df1 = df1[df1['RecordType'] == 'TP']
        df1.columns = df1.columns.str.strip()
        rename_map1 = {
            'ExchangeEBCode': 'CB',
            'TradeDate': 'Date',
            'GiveUpAmt': 'Fee',
            'ClearingAccount': 'Account',
            'Quantity': 'Qty'
        }
        df1 = df1.rename(columns={k: v for k, v in rename_map1.items() if k in df1.columns})
        df2.columns = df2.columns.str.strip()
        rename_map2 = {
            'TGIVIF#': 'CB',
            'TEDATE': 'Date',
            'TFEE5': 'Fee',
            'TQTY': 'Qty',
            'Acct': 'Account'
        }
        df2 = df2.rename(columns={k: v for k, v in rename_map2.items() if k in df2.columns})

        df1['Date'] = pd.to_datetime(df1['Date'].astype(str), format='%Y%m%d', errors='coerce')
        df2['Date'] = pd.to_datetime(df2['Date'].astype(str), format='%Y%m%d', errors='coerce')

        summary1 = df1.groupby(['CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()
        summary2 = df2.groupby(['CB', 'Date', 'Account'], dropna=False)[['Qty', 'Fee']].sum().reset_index()

        summary1 = summary1.rename(columns={'Qty': 'Qty_Atlantis', 'Fee': 'Fee_Atlantis'})
        summary2 = summary2.rename(columns={'Qty': 'Qty_GMI', 'Fee': 'Fee_GMI'})

        matched = pd.merge(summary1, summary2, on=['CB', 'Date', 'Account'], how='inner')
        matched['Qty_Diff'] = matched['Qty_Atlantis'] - matched['Qty_GMI']
        matched['Fee_Diff'] = matched['Fee_Atlantis'] + matched['Fee_GMI']

        left_only = pd.merge(summary1, summary2, on=['CB', 'Date', 'Account'], how='left', indicator=True)
        atlantis_unmatched = left_only[left_only['_merge'] == 'left_only'].drop(columns=['_merge'])

        right_only = pd.merge(summary2, summary1, on=['CB', 'Date', 'Account'], how='left', indicator=True)
        gmi_unmatched = right_only[right_only['_merge'] == 'left_only'].drop(columns=['_merge'])

        final_exceptions = pd.concat([atlantis_unmatched, gmi_unmatched], ignore_index=True)

        st.subheader("Matched Summary")
        st.dataframe(matched)

        st.subheader("Atlantis Unmatched")
        st.dataframe(atlantis_unmatched)

        st.subheader("GMI Unmatched")
        st.dataframe(gmi_unmatched)

        st.subheader("Final Exceptions")
        st.dataframe(final_exceptions)

        # Excel export
        output_file = "gi_recon_output.xlsx"
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            matched.to_excel(writer, sheet_name='Matched', index=False)
            atlantis_unmatched.to_excel(writer, sheet_name='Atlantis_Unmatched', index=False)
            gmi_unmatched.to_excel(writer, sheet_name='GMI_Unmatched', index=False)
            final_exceptions.to_excel(writer, sheet_name='Final_Exceptions', index=False)

        with open(output_file, 'rb') as f:
            st.download_button("Download Results as Excel", f, file_name=output_file)