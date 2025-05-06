
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("📊 GI Reconciliation App with Account Support")

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        df = pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        df = pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None
    return df

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    st.write("🔎 Atlantis columns:", df1.columns.tolist())
    st.write("🔎 GMI columns:", df2.columns.tolist())

    # Rename columns for consistency
    df1 = df1.rename(columns={
        "ExchangeEBCode": "CB",
        "TradeDate": "Date",
        "ClearingAccount": "Account",
        "Quantity": "Qty",
        "GiveUpAmt": "Fee"
    })

    df2 = df2.rename(columns={
        "TGIVIF#": "CB",
        "TEDATE": "Date",
        "Acct": "Account",
        "TQTY": "Qty",
        "TFEE5": "Fee"
    })

    df1["Date"] = pd.to_datetime(df1["Date"]).dt.date
    df2["Date"] = pd.to_datetime(df2["Date"]).dt.date

    df1 = df1.dropna(subset=["CB", "Date", "Account"])
    df2 = df2.dropna(subset=["CB", "Date", "Account"])

    st.write("Filtered Atlantis Sample:", df1[["CB", "Date", "Account"]].head())
    st.write("Filtered GMI Sample:", df2[["CB", "Date", "Account"]].head())

    # Group and summarize
    summary1 = df1.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
    summary2 = df2.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

    summary1 = summary1.rename(columns={"Qty": "Qty_Atlantis", "Fee": "Fee_Atlantis"})
    summary2 = summary2.rename(columns={"Qty": "Qty_GMI", "Fee": "Fee_GMI"})

    merged = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer")
    merged["Qty_Diff"] = merged["Qty_Atlantis"].fillna(0) - merged["Qty_GMI"].fillna(0)
    merged["Fee_Diff"] = merged["Fee_Atlantis"].fillna(0) + merged["Fee_GMI"].fillna(0)

    st.dataframe(merged)
