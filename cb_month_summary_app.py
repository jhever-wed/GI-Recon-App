import streamlit as st
import pandas as pd

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'TGIVF#': 'CB',
        'TEDATE': 'Date',
        'TQTY': 'Qty',
        'TUSDAMT': 'Fee',
        'ACCOUNT': 'Account'
    })
    return df

st.title("Monthly CB Summary")

with st.sidebar:
    atlantis_file = st.file_uploader("Upload Atlantis report", type=["xlsx"])
    gmi_file      = st.file_uploader("Upload GMI report",      type=["xlsx"])

if not atlantis_file or not gmi_file:
    st.warning("Please upload both Atlantis and GMI files.")
    st.stop()

df1 = load_data(atlantis_file)
df2 = load_data(gmi_file)

# add symbol column from each source
df1['symbol'] = df1['PRODUCT']
df2['symbol'] = df2['TFC']

# unify column names
df1['CB'] = df1['CB'].astype(str)
df2['CB'] = df2['CB'].astype(str)

df1['Date'] = pd.to_datetime(df1['Date'], format='%Y%m%d')
df2['Date'] = pd.to_datetime(df2['Date'], format='%Y%m%d')

merged = pd.concat([df1.assign(Source='Atlantis'), df2.assign(Source='GMI')], ignore_index=True)

# monthly rollup
merged['Month'] = merged['Date'].dt.to_period('M')
top_summary = (
    merged
    .groupby(['symbol', 'CB', 'Month'])[['Qty', 'Fee']]
    .sum()
    .reset_index()
)

st.dataframe(top_summary)
