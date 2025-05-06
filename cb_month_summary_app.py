
import streamlit as st
import pandas as pd

st.title("GI Reconciliation App")

def load_file(label):
    uploaded_file = st.file_uploader(f"Upload {label} File", type=["csv", "xls", "xlsx"])
    if uploaded_file is not None:
        ext = uploaded_file.name.split(".")[-1]
        if ext == "csv":
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)
    return None

def preprocess_atlantis(df):
    df = df[df["RecordType"] == "TP"]
    df = df.rename(columns={
        "ExchangeCBCode": "CB",
        "TradeDate": "Date",
        "Quantity": "Qty",
        "GiveUpAmt": "Fee",
        "ClearingAccount": "Account"
    })
    df = df[["CB", "Date", "Qty", "Fee", "Account"]].dropna()
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

def preprocess_gmi(df):
    df = df.rename(columns={
        "TGIVF#": "CB",
        "TEDATE": "Date",
        "TQTY": "Qty",
        "TFEE5": "Fee",
        "Acct": "Account"
    })
    df = df[["CB", "Date", "Qty", "Fee", "Account"]].dropna()
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

atlantis_df = load_file("Atlantis")
gmi_df = load_file("GMI")

if atlantis_df is not None and gmi_df is not None:
    try:
        st.subheader("Preprocessing Data...")
        atlantis_clean = preprocess_atlantis(atlantis_df)
        gmi_clean = preprocess_gmi(gmi_df)
        st.success("Data successfully loaded and cleaned.")

        st.subheader("Sample: Atlantis")
        st.write(atlantis_clean.head())

        st.subheader("Sample: GMI")
        st.write(gmi_clean.head())

        st.subheader("Reconciling...")
        grouped_atlantis = atlantis_clean.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
        grouped_gmi = gmi_clean.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

        final_df = pd.merge(grouped_atlantis, grouped_gmi, on=["CB", "Date", "Account"], how="outer", suffixes=("_Atlantis", "_GMI"))
        final_df["Qty_Diff"] = final_df["Qty_Atlantis"].fillna(0) - final_df["Qty_GMI"].fillna(0)
        final_df["Fee_Diff"] = final_df["Fee_Atlantis"].fillna(0) + final_df["Fee_GMI"].fillna(0)

        st.subheader("Reconciliation Result")
        st.dataframe(final_df)

    except Exception as e:
        st.error(f"Processing Error: {e}")
