import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation – CB & Mismatch", layout="wide")
st.title("📊 GI Reconciliation – CB Summary & Mismatch")

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file, low_memory=False)
    return pd.read_excel(file)

st.sidebar.header("📄 Upload Files")
atlantis_file = st.sidebar.file_uploader("Atlantis CSV/Excel", type=["csv","xls","xlsx"])
gmi_file = st.sidebar.file_uploader("GMI CSV/Excel", type=["csv","xls","xlsx"])

if not (atlantis_file and gmi_file):
    st.info("Please upload both Atlantis and GMI files.")
    st.stop()

df1 = load_data(atlantis_file)
df2 = load_data(gmi_file)
df1.columns = df1.columns.str.strip().str.upper()
df2.columns = df2.columns.str.strip().str.upper()

if "RECORDTYPE" in df1.columns:
    df1 = df1[df1["RECORDTYPE"] == "TP"]

df1 = df1.rename(columns={
    "EXCHANGEEBCODE": "CB", "TRADEDATE": "DATE",
    "QUANTITY": "QTY", "GIVEUPAMT": "FEE", "CLEARINGACCOUNT": "ACCOUNT"
})
rename_map = {}
for col in ["TGIVF#", "TEDATE", "TQTY", "TFEE5"]:
    if col in df2.columns:
        rename_map[col] = {"TGIVF#":"CB", "TEDATE":"DATE", "TQTY":"QTY", "TFEE5":"FEE"}[col]
if "ACCT" in df2.columns:
    rename_map["ACCT"] = "ACCOUNT"
elif "ACCOUNT" in df2.columns:
    rename_map["ACCOUNT"] = "ACCOUNT"
df2 = df2.rename(columns=rename_map)

# Strip CB values to ensure consistency
df1["CB"] = df1["CB"].astype(str).str.strip()
df2["CB"] = df2["CB"].astype(str).str.strip()

df1["DATE"] = pd.to_datetime(df1["DATE"].astype(str), format="%Y%m%d", errors="coerce")
df2["DATE"] = pd.to_datetime(df2["DATE"].astype(str), format="%Y%m%d", errors="coerce")
for c in ["QTY", "FEE"]:
    df1[c] = pd.to_numeric(df1[c], errors="coerce")
    df2[c] = pd.to_numeric(df2[c], errors="coerce")

df1["MONTH"] = df1["DATE"].dt.to_period("M")
df2["MONTH"] = df2["DATE"].dt.to_period("M")
months = sorted(set(df1["MONTH"].dropna()) | set(df2["MONTH"].dropna()))
if not months:
    st.error("No data months")
    st.stop()
sel = st.sidebar.selectbox("Select Month", [m.strftime("%Y-%m") for m in months])
period = pd.Period(sel, freq="M")
df1 = df1[df1["MONTH"] == period]
df2 = df2[df2["MONTH"] == period]

# CB-only summary
s1 = df1.groupby("CB")[["QTY","FEE"]].sum().reset_index().rename(columns={"QTY":"QTY_ATLANTIS","FEE":"FEE_ATLANTIS"})
s2 = df2.groupby("CB")[["QTY","FEE"]].sum().reset_index().rename(columns={"QTY":"QTY_GMI","FEE":"FEE_GMI"})
merged = pd.merge(s1, s2, on="CB", how="outer").fillna(0)
merged["QTY_DIFF"] = merged["QTY_ATLANTIS"] - merged["QTY_GMI"]
merged["FEE_DIFF"] = merged["FEE_ATLANTIS"] + merged["FEE_GMI"]

tab1, tab2 = st.tabs(["CB Summary","Mismatch Summary"])
with tab1:
    st.header("✅ CB Summary")
    st.dataframe(merged)

with tab2:
    details1 = df1.groupby(["CB","DATE","ACCOUNT"])[["QTY","FEE"]].sum().reset_index().rename(columns={"QTY":"QTY_ATLANTIS","FEE":"FEE_ATLANTIS"})
    details2 = df2.groupby(["CB","DATE","ACCOUNT"])[["QTY","FEE"]].sum().reset_index().rename(columns={"QTY":"QTY_GMI","FEE":"FEE_GMI"})
    details = pd.merge(details1, details2, on=["CB","DATE","ACCOUNT"], how="outer").fillna(0)
    details["QTY_DIFF"] = details["QTY_ATLANTIS"] - details["QTY_GMI"]
    details["FEE_DIFF"] = details["FEE_ATLANTIS"] + details["FEE_GMI"]
    mis_details = details[(details["QTY_DIFF"] != 0) | (details["FEE_DIFF"] != 0)]
    st.header("🚫 Mismatch Details (by Date & Account)")
    st.dataframe(mis_details)

st.subheader("📥 Download Full Report")
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    merged.to_excel(writer, sheet_name="CB_Summary", index=False)
    mis_details.to_excel(writer, sheet_name="Mismatch_Summary", index=False)
buf.seek(0)
st.download_button("Download Full Report", buf.getvalue(),
                   file_name=f"full_report_{sel}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
