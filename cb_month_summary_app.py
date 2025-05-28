import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")

st.title("GI Reconciliation App - Summary + Detail Export")

uploaded_file1 = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    # Load files
    df1 = pd.read_csv(uploaded_file1) if uploaded_file1.name.endswith(".csv") else pd.read_excel(uploaded_file1)
    df2 = pd.read_excel(uploaded_file2)

    # Normalize column names
    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    # Filter Atlantis file
    df1 = df1[df1["RECORDTYPE"] == "TP"]

    # Add CB_DATE key
    df1["CB_DATE"] = df1["EXCHANGEEBCODE"].astype(str) + "_" + pd.to_datetime(df1["TRADEDATE"]).dt.strftime("%Y-%m-%d")
    df2["CB_DATE"] = df2["TGIVIF#"].astype(str) + "_" + pd.to_datetime(df2["TEDATE"]).dt.strftime("%Y-%m-%d")

    # Convert numeric
    df1["QUANTITY"] = pd.to_numeric(df1["QUANTITY"], errors="coerce")
    df1["GIVEUPAMT"] = pd.to_numeric(df1["GIVEUPAMT"], errors="coerce")
    df2["TQTY"] = pd.to_numeric(df2["TQTY"], errors="coerce")
    df2["TFEE5"] = pd.to_numeric(df2["TFEE5"], errors="coerce")

    # Group and summarize
    summary1 = df1.groupby(["EXCHANGEEBCODE", pd.to_datetime(df1["TRADEDATE"]).dt.to_period("M")]).agg({
        "QUANTITY": "sum",
        "GIVEUPAMT": "sum"
    }).reset_index()
    summary1["CB"] = summary1["EXCHANGEEBCODE"]
    summary1["MONTH"] = summary1["TRADEDATE"].astype(str)
    summary1.rename(columns={"QUANTITY": "QTY_ATLANTIS", "GIVEUPAMT": "FEE_ATLANTIS"}, inplace=True)

    summary2 = df2.groupby(["TGIVIF#", pd.to_datetime(df2["TEDATE"]).dt.to_period("M")]).agg({
        "TQTY": "sum",
        "TFEE5": "sum"
    }).reset_index()
    summary2["CB"] = summary2["TGIVIF#"]
    summary2["MONTH"] = summary2["TEDATE"].astype(str)
    summary2.rename(columns={"TQTY": "QTY_GMI", "TFEE5": "FEE_GMI"}, inplace=True)

    top_summary = pd.merge(summary1[["CB", "MONTH", "QTY_ATLANTIS", "FEE_ATLANTIS"]],
                           summary2[["CB", "MONTH", "QTY_GMI", "FEE_GMI"]],
                           on=["CB", "MONTH"], how="outer").fillna(0)

    top_summary["QTY_DIFF"] = (top_summary["QTY_ATLANTIS"] - top_summary["QTY_GMI"]).round(2)
    top_summary["FEE_DIFF"] = (top_summary["FEE_ATLANTIS"] + top_summary["FEE_GMI"]).round(2)

    # Show summary
    st.subheader("Summary by CB and Month")
    st.dataframe(top_summary)

    # Detail data for export
    df1["SOURCE"] = "ATLANTIS"
    df2["SOURCE"] = "GMI"
    detail_data = pd.concat([df1, df2], ignore_index=True)

    # Export button
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        top_summary.to_excel(writer, sheet_name="Summary", index=False)
        detail_data.to_excel(writer, sheet_name="Detail", index=False)
    st.download_button("Download Summary + Detail Excel", data=output.getvalue(), file_name="gi_recon_summary_detail.xlsx")