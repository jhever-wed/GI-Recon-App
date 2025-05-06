
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("GI Reconciliation App with Account Field")

def load_data(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "csv":
        df = pd.read_csv(file, dtype=str)
    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file, dtype=str)
    else:
        st.error("Unsupported file type.")
        return None
    df.columns = df.columns.str.strip()
    return df

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)
    
    if df1 is not None and df2 is not None:
        st.success("Files successfully loaded.")
        
        # Normalize and rename columns
        df1 = df1.rename(columns={
            "ExchangeEBCode": "cb",
            "TradeDate": "date",
            "Quantity": "qty",
            "GiveUpAmt": "fee",
            "ClearingAccount": "account"
        })
        df2 = df2.rename(columns={
            "TGIVIF#": "cb",
            "TEDATE": "date",
            "TQTY": "qty",
            "TFEE5": "fee",
            "Acct": "account"
        })

        df1 = df1[["cb", "date", "qty", "fee", "account"]].dropna()
        df2 = df2[["cb", "date", "qty", "fee", "account"]].dropna()

        df1["date"] = pd.to_datetime(df1["date"]).dt.date
        df2["date"] = pd.to_datetime(df2["date"]).dt.date

        df1[["qty", "fee"]] = df1[["qty", "fee"]].apply(pd.to_numeric, errors="coerce").fillna(0)
        df2[["qty", "fee"]] = df2[["qty", "fee"]].apply(pd.to_numeric, errors="coerce").fillna(0)

        summary1 = df1.groupby(["cb", "date", "account"]).agg({"qty": "sum", "fee": "sum"}).reset_index()
        summary2 = df2.groupby(["cb", "date", "account"]).agg({"qty": "sum", "fee": "sum"}).reset_index()

        merged = pd.merge(summary1, summary2, on=["cb", "date", "account"], how="outer", suffixes=("_atlantis", "_gmi"))
        merged.fillna(0, inplace=True)
        merged["qty_diff"] = merged["qty_atlantis"] - merged["qty_gmi"]
        merged["fee_diff"] = merged["fee_atlantis"] + merged["fee_gmi"]

        st.dataframe(merged)

        # Export button
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            merged.to_excel(writer, index=False, sheet_name="Reconciliation")
        st.download_button("📥 Download Excel", output.getvalue(), file_name="gi_reconciliation_output.xlsx")
