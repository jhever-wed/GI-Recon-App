
import streamlit as st
import pandas as pd

st.title("GI Reconciliation App")

def load_data(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "csv":
        return pd.read_csv(file)
    elif ext in ["xls", "xlsx"]:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file format")
        return None

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        # Rename for consistency
        df1.rename(columns={"ClearingAccount": "Account", "ExchangeEBCode": "CB", "TradeDate": "Date", "Quantity": "Qty", "GiveUpAmt": "Fee"}, inplace=True)
        df2.rename(columns={"Acct": "Account", "TGIVIF#": "CB", "TEDATE": "Date", "TQTY": "Qty", "TFEE5": "Fee"}, inplace=True)

        try:
            df1["Date"] = pd.to_datetime(df1["Date"]).dt.date
            df2["Date"] = pd.to_datetime(df2["Date"]).dt.date

            df1 = df1[["CB", "Date", "Qty", "Fee", "Account"]].dropna()
            df2 = df2[["CB", "Date", "Qty", "Fee", "Account"]].dropna()

            summary1 = df1.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
            summary2 = df2.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

            result = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer", suffixes=('_Atlantis', '_GMI'))
            result.fillna(0, inplace=True)
            result["Qty_Diff"] = result["Qty_Atlantis"] - result["Qty_GMI"]
            result["Fee_Diff"] = result["Fee_Atlantis"] + result["Fee_GMI"]

            st.dataframe(result)

        except Exception as e:
            st.error(f"Processing Error: {e}")
