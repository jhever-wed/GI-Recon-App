
import io
import pandas as pd
import streamlit as st

def load_data(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    return df

st.title("📅 CB Month Summary")

# File upload
atlantis_file = st.sidebar.file_uploader("Upload Atlantis file")
gmi_file = st.sidebar.file_uploader("Upload GMI file")

# Month selector
month_options = ["-- Select Month --"]
if atlantis_file:
    df1 = load_data(atlantis_file)
    month_options += sorted(df1['DATE'].str[:7].unique().tolist())
if gmi_file:
    df2 = load_data(gmi_file)
    month_options += sorted(df2['TEDATE'].str[:7].unique().tolist())

month = st.sidebar.selectbox("Select Month", month_options)

# Require month selection before running
if month == "-- Select Month --":
    st.sidebar.warning("⚠️ Please select a month before running the report.")
    st.stop()

# After month selected, process data
df1 = load_data(atlantis_file)
df2 = load_data(gmi_file)

# Filter by month
df1 = df1[df1['DATE'].str.startswith(month)]
df2 = df2[df2['TEDATE'].str.startswith(month)]

# Rename and add symbol
df1 = df1.rename(columns={'PRODUCT': 'SYM', 'TGIVF#': 'CB', 'TEDATE': 'DATE', 'TQTY': 'Qty', 'TFEE': 'Fee', 'ACCT': 'Account'})
df1['SYM'] = df1['SYM']
df2 = df2.rename(columns={'TFC': 'SYM', 'TGIVF#': 'CB', 'TEDATE': 'DATE', 'TQTY': 'Qty', 'TFEE': 'Fee', 'ACCT': 'Account'})
df2['SYM'] = df2['SYM']

# Summarize
summary1 = df1.groupby(['SYM', 'CB', 'DATE', 'Account'])[['Qty', 'Fee']].sum().reset_index().rename(columns={'Qty': 'Qty_Atlantis', 'Fee': 'Fee_Atlantis'})
summary2 = df2.groupby(['SYM', 'CB', 'DATE', 'Account'])[['Qty', 'Fee']].sum().reset_index().rename(columns={'Qty': 'Qty_GMI', 'Fee': 'Fee_GMI'})

# Merge and display
merged = pd.merge(summary1, summary2, on=['SYM', 'CB', 'DATE', 'Account'], how='outer').fillna(0)
st.header("📊 Merged Summary")
st.dataframe(merged)

# Download
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    merged.to_excel(writer, index=False, sheet_name='Summary')
output.seek(0)
st.download_button("Download Excel", data=output, file_name=f"CB_Summary_{month}.xlsx")
