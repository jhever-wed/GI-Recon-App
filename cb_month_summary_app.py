import streamlit as st
import pandas as pd
from io import BytesIO

st.title("GI Recon - Summary & Detail Export")

uploaded_file1 = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    # Read files and normalize columns
    df1 = pd.read_csv(uploaded_file1) if uploaded_file1.name.endswith(".csv") else pd.read_excel(uploaded_file1)
    df2 = pd.read_csv(uploaded_file2) if uploaded_file2.name.endswith(".csv") else pd.read_excel(uploaded_file2)

    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    # Convert numeric columns
    df1["QUANTITY"] = pd.to_numeric(df1["QUANTITY"], errors="coerce")
    df1["GIVEUPAMT"] = pd.to_numeric(df1["GIVEUPAMT"], errors="coerce")
    df2["TQTY"] = pd.to_numeric(df2["TQTY"], errors="coerce")
    df2["TFEE5"] = pd.to_numeric(df2["TFEE5"], errors="coerce")

    df1["TRADEDATE"] = pd.to_datetime(df1["TRADEDATE"], errors="coerce")
    df2["TEDATE"] = pd.to_datetime(df2["TEDATE"], errors="coerce")

    # Add CB-Date key
    df1["CB_DATE"] = df1["EXCHANGEEBCODE"].astype(str) + "_" + df1["TRADEDATE"].dt.strftime("%Y-%m-%d")
    df2["CB_DATE"] = df2["TGIVIF#"].astype(str) + "_" + df2["TEDATE"].dt.strftime("%Y-%m-%d")

    # Group summaries
    summary1 = df1.groupby(["EXCHANGEEBCODE", df1["TRADEDATE"].dt.to_period("M")]).agg({
        "QUANTITY": "sum", "GIVEUPAMT": "sum"
    }).reset_index()
    summary1.columns = ["CB", "Month", "QTY_ATLANTIS", "FEE_ATLANTIS"]

    summary2 = df2.groupby(["TGIVIF#", df2["TEDATE"].dt.to_period("M")]).agg({
        "TQTY": "sum", "TFEE5": "sum"
    }).reset_index()
    summary2.columns = ["CB", "Month", "QTY_GMI", "FEE_GMI"]

    # Merge summaries
    top_summary = pd.merge(summary1, summary2, on=["CB", "Month"], how="outer").fillna(0)
    top_summary["QTY_DIFF"] = (top_summary["QTY_ATLANTIS"] - top_summary["QTY_GMI"]).round(2)
    top_summary["FEE_DIFF"] = (top_summary["FEE_ATLANTIS"] - top_summary["FEE_GMI"]).round(2)

    st.subheader("Summary")
    st.dataframe(top_summary)

    st.subheader("Detail")
    df1["SOURCE"] = "ATLANTIS"
    df2["SOURCE"] = "GMI"
    detail_df = pd.concat([df1, df2], ignore_index=True)
    st.dataframe(detail_df)

    # Export to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        top_summary.to_excel(writer, index=False, sheet_name="Summary")
        detail_df.to_excel(writer, index=False, sheet_name="Detail")
    st.download_button("Download Excel Export", data=output.getvalue(), file_name="recon_summary_export.xlsx")