import streamlit as st
import pandas as pd
import io

# Page config
st.set_page_config(page_title="GI Reconciliation", layout="wide")
st.title("📊 GI Reconciliation Dashboard")

# Data loader
def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file, low_memory=False)
    return pd.read_excel(file)

# Sidebar uploads
st.sidebar.header("📄 Upload Files")
atlantis_file = st.sidebar.file_uploader("Upload Atlantis File", type=["csv","xls","xlsx"])
gmi_file      = st.sidebar.file_uploader("Upload GMI File",     type=["csv","xls","xlsx"])

if not (atlantis_file and gmi_file):
    st.info("Please upload both Atlantis and GMI files to continue.")
    st.stop()

# Load dataframes
df1 = load_data(atlantis_file)
df2 = load_data(gmi_file)

# Standardize column names to uppercase trimmed
df1.columns = df1.columns.str.strip().str.upper()
df2.columns = df2.columns.str.strip().str.upper()

# Filter Atlantis by RecordType 'TP' if present
if "RECORDTYPE" in df1.columns:
    df1 = df1[df1["RECORDTYPE"] == "TP"]

# Rename to known
df1 = df1.rename(columns={
    "EXCHANGEEBCODE": "CB",
    "TRADEDATE": "DATE",
    "QUANTITY": "QTY",
    "GIVEUPAMT": "FEE",
    "CLEARINGACCOUNT": "ACCOUNT"
})
# Map GMI columns
rename_map = {}
for key, up in [("TGIVF#", "CB"), ("TEDATE", "DATE"), ("TQTY", "QTY"), ("TFEE5", "FEE")]:
    if key in df2:
        rename_map[key] = up
# Account mapping
if "ACCT" in df2:
    rename_map["ACCT"] = "ACCOUNT"
elif "ACCOUNT" in df2:
    rename_map["ACCOUNT"] = "ACCOUNT"
else:
    st.error("Missing 'Acct' column in GMI file.")
    st.stop()
df2 = df2.rename(columns=rename_map)

# Parse types
df1["DATE"] = pd.to_datetime(df1["DATE"].astype(str), format="%Y%m%d", errors="coerce")
df2["DATE"] = pd.to_datetime(df2["DATE"].astype(str), format="%Y%m%d", errors="coerce")
for c in ["QTY","FEE"]:
    df1[c] = pd.to_numeric(df1[c], errors="coerce")
    df2[c] = pd.to_numeric(df2[c], errors="coerce")

# Month selection
df1["MONTH"] = df1["DATE"].dt.to_period("M")
df2["MONTH"] = df2["DATE"].dt.to_period("M")
months = sorted(set(df1["MONTH"].dropna()) | set(df2["MONTH"].dropna()))
if not months:
    st.error("No data available for month selection.")
    st.stop()
month_strs = [m.strftime("%Y-%m") for m in months]
selected_str = st.sidebar.selectbox("Select Month", month_strs)
period = pd.Period(selected_str, freq="M")
df1 = df1[df1["MONTH"] == period]
df2 = df2[df2["MONTH"] == period]

# Summaries
s1 = df1.groupby(["CB","DATE","ACCOUNT"], dropna=False)[["QTY","FEE"]].sum().reset_index()
s1 = s1.rename(columns={"QTY": "QTY_ATLANTIS", "FEE": "FEE_ATLANTIS"})
s2 = df2.groupby(["CB","DATE","ACCOUNT"], dropna=False)[["QTY","FEE"]].sum().reset_index()
s2 = s2.rename(columns={"QTY": "QTY_GMI",     "FEE": "FEE_GMI"})

merged = pd.merge(s1, s2, on=["CB","DATE","ACCOUNT"], how="outer").fillna(0)
merged["QTY_DIFF"] = merged["QTY_ATLANTIS"] - merged["QTY_GMI"]
merged["FEE_DIFF"] = merged["FEE_ATLANTIS"] + merged["FEE_GMI"]

# Layout tabs
tab1, tab2 = st.tabs(["CB Summary", "Mismatch Summary"])
with tab1:
    st.header("✅ CB Summary")
    st.dataframe(merged[[
        "CB","DATE","ACCOUNT",
        "QTY_ATLANTIS","FEE_ATLANTIS",
        "QTY_GMI","FEE_GMI",
        "QTY_DIFF","FEE_DIFF"
    ]])
with tab2:
    mis = merged[(merged["QTY_DIFF"] != 0) | (merged["FEE_DIFF"] != 0)]
    st.header("🚫 Mismatch Summary by Account & Date")
    st.dataframe(mis)

# Unified download
st.subheader("📥 Download Full Report")
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    merged.to_excel(writer, sheet_name="CB_Summary", index=False)
    mis.to_excel(writer, sheet_name="Mismatch_Summary", index=False)
buf.seek(0)
st.download_button(
    label="Download Full Report",
    data=buf.getvalue(),
    file_name=f"full_report_{selected_str}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
