
import io
import pandas as pd
import streamlit as st

def load_data(filepath):
    """Load CSV with utf-8 or latin1 fallback and strip columns."""
    try:
        df = pd.read_csv(filepath)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding='latin1')
    df.columns = df.columns.str.strip()
    # Normalize date column names
    for col in df.columns:
        if col.upper().startswith('DATE'):
            df = df.rename(columns={col: 'Date'})
        elif col.upper().startswith('TEDATE'):
            df = df.rename(columns={col: 'Date'})
    return df


st.title("📅 CB Month Summary")

# File upload (accept any file)
atlantis_file = st.sidebar.file_uploader("Upload Atlantis file", type=None)
gmi_file = st.sidebar.file_uploader("Upload GMI file", type=None)

# Month selector
st.sidebar.markdown("### Select Month")
month = st.sidebar.selectbox("Month", ["-- Select Month --"] + pd.date_range(start="2000-01-01", end=pd.Timestamp.today(), freq='ME').strftime('%Y-%m').tolist())
if month == "-- Select Month --":
    st.sidebar.warning("⚠️ Please select a month before running the report.")
    st.stop()

# Load data
if atlantis_file:
    df1 = load_data(atlantis_file)
else:
    st.sidebar.warning("⚠️ Please upload the Atlantis file.")
    st.stop()

if gmi_file:
    df2 = load_data(gmi_file)
else:
    st.sidebar.warning("⚠️ Please upload the GMI file.")
    st.stop()

# Filter by selected month
df1 = df1[df1['DATE'].astype(str).str.startswith(month)]
df2 = df2[df2['DATE'].astype(str).str.startswith(month)]

# Summarize
summary1 = df1.groupby(['SYM', 'CB', 'DATE', 'Account'])[['Qty', 'Fee']].sum().reset_index()
summary1 = summary1.rename(columns={'Qty': 'Qty_Atlantis', 'Fee': 'Fee_Atlantis'})

summary2 = df2.groupby(['SYM', 'CB', 'DATE', 'Account'])[['Qty', 'Fee']].sum().reset_index()
summary2 = summary2.rename(columns={'Qty': 'Qty_GMI', 'Fee': 'Fee_GMI'})

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
