
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="GI Recon App", layout="wide")

st.title("GI Reconciliation App")

def load_data(file):
    try:
        ext = file.name.split(".")[-1]
        if ext == "csv":
            df = pd.read_csv(file)
        elif ext in ["xls", "xlsx"]:
            df = pd.read_excel(file)
        else:
            st.error("Unsupported file type")
            return None
        return df
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

atlantis_file = st.file_uploader("Upload Atlantis file (CSV/XLSX)", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI file (CSV/XLSX)", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        st.write("✅ Files loaded.")
        st.write("Atlantis Columns:", df1.columns.tolist())
        st.write("GMI Columns:", df2.columns.tolist())

        # Rename columns
        df1 = df1.rename(columns={"ExchangeEBCode": "CB", "TradeDate": "Date", "Quantity": "Qty", "GiveUpAmt": "Fee", "ClearingAccount": "Account"})
        df2 = df2.rename(columns={"TGIVIF#": "CB", "TEDATE": "Date", "TQTY": "Qty", "TFEE5": "Fee", "Acct": "Account"})

        # Ensure date columns are proper
        df1["Date"] = pd.to_datetime(df1["Date"], errors='coerce').dt.date
        df2["Date"] = pd.to_datetime(df2["Date"], errors='coerce').dt.date

        # Filter out rows with missing key fields
        df1 = df1.dropna(subset=["CB", "Date", "Account"])
        df2 = df2.dropna(subset=["CB", "Date", "Account"])

        st.write("🔍 Filtered Atlantis Sample:", df1[["CB", "Date", "Account"]].head())
        st.write("🔍 Filtered GMI Sample:", df2[["CB", "Date", "Account"]].head())

        try:
            summary1 = df1.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()
            summary2 = df2.groupby(["CB", "Date", "Account"]).agg({"Qty": "sum", "Fee": "sum"}).reset_index()

            summary1 = summary1.rename(columns={"Qty": "Qty_Atlantis", "Fee": "Fee_Atlantis"})
            summary2 = summary2.rename(columns={"Qty": "Qty_GMI", "Fee": "Fee_GMI"})

            merged = pd.merge(summary1, summary2, on=["CB", "Date", "Account"], how="outer")

            for col in ["Qty_Atlantis", "Fee_Atlantis", "Qty_GMI", "Fee_GMI"]:
                merged[col] = merged[col].fillna(0)

            merged["Qty_Diff"] = merged["Qty_Atlantis"] - merged["Qty_GMI"]
            merged["Fee_Diff"] = merged["Fee_Atlantis"] + merged["Fee_GMI"]

            st.subheader("📊 Matched Summary")
            st.dataframe(merged)

            # Export
            st.subheader("📥 Download Reconciliation")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                merged.to_excel(writer, sheet_name="Matched", index=False)
            st.download_button("Download Excel", data=buffer.getvalue(), file_name="reconciliation_output.xlsx")
        except Exception as e:
            st.error(f"❌ Error during processing: {e}")
