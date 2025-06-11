import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation", layout="wide")
st.title("📊 GI Reconciliation – CB Summary & Mismatch")

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file, low_memory=False)
    else:
        return pd.read_excel(file)

# Sidebar uploads
st.sidebar.header("📄 Upload Files")
atlantis = st.sidebar.file_uploader("Atlantis CSV/Excel", type=["csv","xls","xlsx"])
gmi      = st.sidebar.file_uploader("GMI  CSV/Excel",     type=["csv","xls","xlsx"])

if not (atlantis and gmi):
    st.info("Please upload both Atlantis and GMI files.")
    st.stop()

# Load Data
df1 = load_data(atlantis)
df2 = load_data(gmi)

# Standardize column names to uppercase
df1.columns = df1.columns.str.strip().str.upper()
df2.columns = df2.columns.str.strip().str.upper()

# Atlantis filter
if "RECORDTYPE" in df1.columns:
    df1 = df1[df1["RECORDTYPE"]=="TP"]

# Rename to known names
df1 = df1.rename(columns={
    "EXCHANGEEBCODE":"CB",
    "TRADEDATE":"DATE",
    "QUANTITY":"QTY",
    "GIVEUPAMT":"FEE",
    "CLEARINGACCOUNT":"ACCOUNT"
})
df2 = df2.rename(columns={
    "TGIVF#":"CB",
    "TEDATE":"DATE",
    "TQTY":"QTY",
    "TFEE5":"FEE",
    **({"ACCT":"ACCOUNT"} if "ACCT" in df2.columns else {}),
    **({"ACCOUNT":"ACCOUNT"} if "ACCOUNT" in df2.columns else {})
})

# Parse types
df1["DATE"] = pd.to_datetime(df1["DATE"], format="%Y%m%d", errors="coerce")
df2["DATE"] = pd.to_datetime(df2["DATE"], format="%Y%m%d", errors="coerce")
for c in ["QTY","FEE"]:
    df1[c] = pd.to_numeric(df1[c], errors="coerce")
    df2[c] = pd.to_numeric(df2[c], errors="coerce")

# Month selector
df1["MONTH"] = df1["DATE"].dt.to_period("M")
df2["MONTH"] = df2["DATE"].dt.to_period("M")
months = sorted(set(df1["MONTH"].dropna()) | set(df2["MONTH"].dropna()))
if not months:
    st.error("No data months found.")
    st.stop()
sel = st.sidebar.selectbox("Select Month", [m.strftime("%Y-%m") for m in months])
period = pd.Period(sel, freq="M")
df1 = df1[df1["MONTH"]==period]
df2 = df2[df2["MONTH"]==period]

# Summaries
s1 = (df1.groupby(["CB","DATE","ACCOUNT"], dropna=False)[["QTY","FEE"]]
      .sum().reset_index().rename(columns={"QTY":"QTY_ATLANTIS","FEE":"FEE_ATLANTIS"}))
s2 = (df2.groupby(["CB","DATE","ACCOUNT"], dropna=False)[["QTY","FEE"]]
      .sum().reset_index().rename(columns={"QTY":"QTY_GMI","FEE":"FEE_GMI"}))

merged = pd.merge(s1, s2, on=["CB","DATE","ACCOUNT"], how="outer").fillna(0)
merged["QTY_DIFF"] = merged["QTY_ATLANTIS"] - merged["QTY_GMI"]
merged["FEE_DIFF"] = merged["FEE_ATLANTIS"] + merged["FEE_GMI"]

# Tabs
tab1, tab2 = st.tabs(["CB Summary","Mismatch Summary"])
with tab1:
    st.header("✅ CB Summary")
    st.dataframe(merged[[
        "CB","DATE","ACCOUNT",
        "QTY_ATLANTIS","FEE_ATLANTIS",
        "QTY_GMI","FEE_GMI",
        "QTY_DIFF","FEE_DIFF"
    ]])
with tab2:
    mis = merged[(merged["QTY_DIFF"]!=0)|(merged["FEE_DIFF"]!=0)]
    st.header("🚫 Mismatch Summary by Account & Date")
    st.dataframe(mis)

# Download both sheets
st.subheader("📥 Download Full Report")
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    merged.to_excel(writer, sheet_name="CB_Summary", index=False)
    mis.to_excel(writer, sheet_name="Mismatch_Summary", index=False)
buf.seek(0)
st.download_button("Download Full Report", buf.getvalue(),
                   file_name=f"full_report_{sel}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
