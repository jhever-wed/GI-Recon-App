
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("GI Reconciliation App with Account (Step 2)")

def load_data(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "csv":
        return pd.read_csv(file, low_memory=False)
    elif ext in ["xls", "xlsx"]:
        try:
            return pd.read_excel(file, engine="openpyxl")
        except Exception as e:
            st.error(f"Failed to read Excel file: {e}")
            return None
    else:
        st.error("Unsupported file type.")
        return None

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        try:
            df1 = df1[df1["RecordType"] == "TP"]
            df1["Date"] = pd.to_datetime(df1["TradeDate"].astype(str), errors="coerce")
            df2["Date"] = pd.to_datetime(df2["TEDATE"].astype(str), errors="coerce")

            df1["CB"] = df1["ExchangeEBCode"]
            df2["CB"] = df2["TGIVIF#"]

            df1["Qty"] = pd.to_numeric(df1["Quantity"], errors="coerce")
            df1["Fee"] = pd.to_numeric(df1["GiveUpAmt"], errors="coerce")
            df1["Account"] = df1["ClearingAccount"]

            df2["Qty"] = pd.to_numeric(df2["TQTY"], errors="coerce")
            df2["Fee"] = pd.to_numeric(df2["TFEE5"], errors="coerce")
            df2["Account"] = df2["Acct"]

            summary1 = df1.groupby(["CB", "Date", "Account"], dropna=False).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
            summary2 = df2.groupby(["CB", "Date", "Account"], dropna=False).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

            summary1 = summary1.rename(columns={"Qty": "Qty_Atlantis", "Fee": "Fee_Atlantis"})
            summary2 = summary2.rename(columns={"Qty": "Qty_GMI", "Fee": "Fee_GMI"})

            merged = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer")

            for col in ["Qty_Atlantis", "Fee_Atlantis", "Qty_GMI", "Fee_GMI"]:
                merged[col] = merged[col].fillna(0)

            merged["Qty_Diff"] = merged["Qty_Atlantis"] - merged["Qty_GMI"]
            merged["Fee_Diff"] = merged["Fee_Atlantis"] + merged["Fee_GMI"]

            st.subheader("Reconciliation Results")
            st.dataframe(merged)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                merged.to_excel(writer, index=False, sheet_name="Reconciliation")
            st.download_button("📥 Download Reconciliation", data=buffer.getvalue(), file_name="reconciliation_output.xlsx")
        except Exception as e:
            st.error(f"An error occurred during reconciliation: {e}")
