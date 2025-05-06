
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("GI Reconciliation App")

def load_data(file):
    ext = file.name.split('.')[-1]
    if ext == 'csv':
        return pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

st.info("Upload Atlantis (CSV) and GMI (Excel) files")

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv"], key="atlantis")
gmi_file = st.file_uploader("Upload GMI File", type=["xls", "xlsx"], key="gmi")

if atlantis_file and gmi_file:
    st.success("Files uploaded. Processing...")

    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        df1 = df1[df1['RecordType'] == 'TP']

        df1 = df1.rename(columns={
            "ExchangeEBCode": "CB",
            "TradeDate": "Date",
            "ClearingAccount": "Account",
            "Quantity": "Qty",
            "GiveUpAmt": "Fee",
        })

        df2 = df2.rename(columns={
            "TGIVIF#": "CB",
            "TEDATE": "Date",
            "Acct": "Account",
            "TQTY": "Qty",
            "TFEE5": "Fee",
        })

        df1["Date"] = pd.to_datetime(df1["Date"]).dt.date
        df2["Date"] = pd.to_datetime(df2["Date"]).dt.date

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

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            merged.to_excel(writer, index=False, sheet_name="Reconciliation")
        st.download_button("Download Reconciliation Report", buffer.getvalue(), file_name="reconciliation_output.xlsx")
