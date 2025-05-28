
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("GI Reconciliation - Simplified")

uploaded_file1 = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    # Load and standardize
    df1 = pd.read_csv(uploaded_file1) if uploaded_file1.name.endswith(".csv") else pd.read_excel(uploaded_file1)
    df2 = pd.read_excel(uploaded_file2)

    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    # Filter
    df1 = df1[df1["RECORDTYPE"] == "TR"]

    # Ensure date columns are datetime
    df1["TRADEDATE"] = pd.to_datetime(df1["TRADEDATE"], errors="coerce")
    df2["TEDATE"] = pd.to_datetime(df2["TEDATE"], errors="coerce")

    # Normalize numerics
    df1["QUANTITY"] = pd.to_numeric(df1["QUANTITY"], errors="coerce")
    df1["GIVEUPAMT"] = pd.to_numeric(df1["GIVEUPAMT"], errors="coerce")
    df1["GIVEUPRATE"] = pd.to_numeric(df1["GIVEUPRATE"], errors="coerce")

    df2["TQTY"] = pd.to_numeric(df2["TQTY"], errors="coerce")
    df2["TFEE5"] = pd.to_numeric(df2["TFEE5"], errors="coerce")

    # Keys
    df1["CB_DATE"] = df1["EXCHANGEEBCODE"].astype(str) + "_" + df1["TRADEDATE"].dt.strftime("%Y-%m-%d")
    df2["CB_DATE"] = df2["TGIVF#"].astype(str) + "_" + df2["TEDATE"].dt.strftime("%Y-%m-%d")

    df1["CB"] = df1["EXCHANGEEBCODE"]
    df2["CB"] = df2["TGIVF#"]

    # Summarize
    summary1 = df1.groupby("CB")[["QUANTITY", "GIVEUPAMT"]].sum().rename(columns={"QUANTITY": "QTY_ATLANTIS", "GIVEUPAMT": "FEE_ATLANTIS"})
    summary2 = df2.groupby("CB")[["TQTY", "TFEE5"]].sum().rename(columns={"TQTY": "QTY_GMI", "TFEE5": "FEE_GMI"})
    top_summary = summary1.join(summary2, how="outer").fillna(0)
    top_summary["QTY_DIFF"] = (top_summary["QTY_ATLANTIS"] - top_summary["QTY_GMI"]).round(2)
    top_summary["FEE_DIFF"] = (top_summary["FEE_ATLANTIS"] + top_summary["FEE_GMI"]).round(2)

    st.subheader("Section 1: Summary by CB")
    st.dataframe(top_summary)

    # Detail merge
    cols1 = ["CB_DATE", "EXCHANGEEBCODE", "TRADEDATE", "QUANTITY", "GIVEUPAMT", "GIVEUPRATE", "CLEARINGACCOUNT"]
    cols2 = ["CB_DATE", "TGIVF#", "TEDATE", "TQTY", "TFEE5", "ACCT"]
    df1_detail = df1[cols1].rename(columns={
        "EXCHANGEEBCODE": "CB",
        "TRADEDATE": "DATE",
        "QUANTITY": "QTY_ATLANTIS",
        "GIVEUPAMT": "FEE_ATLANTIS",
        "GIVEUPRATE": "RATE_ATLANTIS",
        "CLEARINGACCOUNT": "ACCOUNT_ATLANTIS"
    })
    df2_detail = df2[cols2].rename(columns={
        "TGIVF#": "CB",
        "TEDATE": "DATE",
        "TQTY": "QTY_GMI",
        "TFEE5": "FEE_GMI",
        "ACCT": "ACCOUNT_GMI"
    })

    merged = pd.merge(df1_detail, df2_detail, on="CB_DATE", how="outer")
    merged["QTY_DIFF"] = (merged["QTY_ATLANTIS"].fillna(0) - merged["QTY_GMI"].fillna(0)).round(2)
    merged["FEE_DIFF"] = (merged["FEE_ATLANTIS"].fillna(0) + merged["FEE_GMI"].fillna(0)).round(2)

    st.subheader("Section 2: Detail Rows")
    st.dataframe(merged)

    # Export logic
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        top_summary.to_excel(writer, index=True, sheet_name="Summary")
        merged.to_excel(writer, index=False, sheet_name="Detail")
    st.download_button("Download Results as Excel", data=output.getvalue(), file_name="gi_recon_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
