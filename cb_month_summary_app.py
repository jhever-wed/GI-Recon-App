
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Reconciliation", layout="wide")
st.title("GI Reconciliation App")

def load_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, low_memory=False)
    elif file.name.endswith((".xls", ".xlsx")):
        df = pd.read_excel(file)
    else:
        st.error("Unsupported file format")
        return None
    return df

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        st.success("Files loaded successfully")

        # Rename columns BEFORE filtering
        df1 = df1.rename(columns={
            "ExchangeEBCode": "CB",
            "ClearingAccount": "Account",
            "TradeDate": "Date",
            "Quantity": "Qty",
            "GiveUpAmt": "Fee"
        })

        df2 = df2.rename(columns={
            "TGIVIF#": "CB",
            "Acct": "Account",
            "TEDATE": "Date",
            "TQTY": "Qty",
            "TFEE5": "Fee"
        })

        df1["Date"] = pd.to_datetime(df1["Date"]).dt.date
        df2["Date"] = pd.to_datetime(df2["Date"]).dt.date

        df1 = df1.dropna(subset=["CB", "Date", "Account"])
        df2 = df2.dropna(subset=["CB", "Date", "Account"])

        st.write("Filtered Atlantis Sample:", df1[["CB", "Date", "Account"]].head())
        st.write("Filtered GMI Sample:", df2[["CB", "Date", "Account"]].head())

        # Aggregate
        summary1 = df1.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
        summary2 = df2.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

        summary1 = summary1.rename(columns={"Qty": "Qty_Atlantis", "Fee": "Fee_Atlantis"})
        summary2 = summary2.rename(columns={"Qty": "Qty_GMI", "Fee": "Fee_GMI"})

        merged = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer")

        for col in ["Qty_Atlantis", "Fee_Atlantis", "Qty_GMI", "Fee_GMI"]:
            merged[col] = merged[col].fillna(0)

        merged["Qty_Diff"] = merged["Qty_Atlantis"] - merged["Qty_GMI"]
        merged["Fee_Diff"] = merged["Fee_Atlantis"] + merged["Fee_GMI"]

        st.dataframe(merged)
