import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("GI Reconciliation App")

def load_data(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(file)
    else:
        st.error("Unsupported file type.")
        return None

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    st.info("Reading input files...")
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        st.info("Renaming columns...")
        df1 = df1[df1['RecordType'] == 'TP']
        df1 = df1.rename(columns={
            "ExchangeEBCode": "CB",
            "TradeDate": "Date",
            "Quantity": "Qty",
            "GiveUpAmt": "Fee",
            "ClearingAccount": "Account"
        })
        df2 = df2.rename(columns={
            "TGIVIF#": "CB",
            "TEDATE": "Date",
            "TQTY": "Qty",
            "TFEE5": "Fee",
            "Acct": "Account"
        })

        st.info("Converting date formats...")
        df1["Date"] = pd.to_datetime(df1["Date"]).dt.date
        df2["Date"] = pd.to_datetime(df2["Date"]).dt.date

        st.info("Aggregating summaries...")
        summary1 = df1.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
        summary2 = df2.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

        summary1 = summary1.rename(columns={"Qty": "Qty_Atlantis", "Fee": "Fee_Atlantis"})
        summary2 = summary2.rename(columns={"Qty": "Qty_GMI", "Fee": "Fee_GMI"})

        st.info("Merging summaries...")
        merged = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer")

        for col in ["Qty_Atlantis", "Fee_Atlantis", "Qty_GMI", "Fee_GMI"]:
            merged[col] = merged[col].fillna(0)

        merged["Qty_Diff"] = merged["Qty_Atlantis"] - merged["Qty_GMI"]
        merged["Fee_Diff"] = merged["Fee_Atlantis"] + merged["Fee_GMI"]

        st.dataframe(merged)

        st.subheader("📥 Export All Sections to Excel")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            merged.to_excel(writer, sheet_name="Matched", index=False)
        st.download_button("Download Excel", buffer.getvalue(), file_name="gi_reconciliation_output.xlsx", mime="application/vnd.ms-excel")