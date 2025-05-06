
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")
st.title("GI Reconciliation App")

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    if ext == 'csv':
        return pd.read_csv(file)
    elif ext in ['xls', 'xlsx']:
        return pd.read_excel(file)
    else:
        st.error("Unsupported file format.")
        return None

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        # Rename columns first
        df1 = df1.rename(columns={"ExchangeEBCode": "CB", "TradeDate": "Date", "ClearingAccount": "Account"})
        df2 = df2.rename(columns={"TGIVIF#": "CB", "TEDATE": "Date", "Acct": "Account"})

        # Convert date fields
        df1["Date"] = pd.to_datetime(df1["Date"], errors="coerce").dt.date
        df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce").dt.date

        # Drop rows with missing critical fields
        df1 = df1.dropna(subset=["CB", "Date", "Account"])
        df2 = df2.dropna(subset=["CB", "Date", "Account"])

        st.write("Atlantis Sample:", df1[["CB", "Date", "Account"]].head())
        st.write("GMI Sample:", df2[["CB", "Date", "Account"]].head())

        # Summarize
        summary1 = df1.groupby(["CB", "Date", "Account"]).agg({"Quantity": "sum", "GiveUpAmt": "sum"}).reset_index()
        summary2 = df2.groupby(["CB", "Date", "Account"]).agg({"TQTY": "sum", "TFEE5": "sum"}).reset_index()

        summary1 = summary1.rename(columns={"Quantity": "Qty_Atlantis", "GiveUpAmt": "Fee_Atlantis"})
        summary2 = summary2.rename(columns={"TQTY": "Qty_GMI", "TFEE5": "Fee_GMI"})

        merged = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer")
        merged = merged.fillna(0)
        merged["Qty_Diff"] = merged["Qty_Atlantis"] - merged["Qty_GMI"]
        merged["Fee_Diff"] = merged["Fee_Atlantis"] + merged["Fee_GMI"]

        st.subheader("🔍 Reconciliation Summary")
        st.dataframe(merged)

        # Download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            merged.to_excel(writer, index=False, sheet_name="Summary")
        st.download_button("📥 Download Excel", buffer.getvalue(), file_name="reconciliation_summary.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
