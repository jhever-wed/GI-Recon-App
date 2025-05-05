import streamlit as st
import pandas as pd

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

st.title("GI Reconciliation App (Account Fields Step 1)")

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    st.info('Loading Atlantis file...')
    df1 = load_data(atlantis_file)

    st.info('Loading GMI file...')
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        st.info('Filtering Atlantis to RecordType == TP')
        df1 = df1[df1['RecordType'] == 'TP']

        st.info('Renaming columns')
        df1 = df1.rename(columns={
            'ExchangeEBCode': 'CB',
            'TradeDate': 'Date',
            'GiveUpAmt': 'Fee',
            'ClearingAccount': 'Account',
            'Quantity': 'Qty'
        })

        df2 = df2.rename(columns={
            'TGIVIF#': 'CB',
            'TEDATE': 'Date',
            'TFEE5': 'Fee',
            'Acct': 'Account',
            'TQTY': 'Qty'
        })

        st.success("Files loaded and columns renamed successfully.")