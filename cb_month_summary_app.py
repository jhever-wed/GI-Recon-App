
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")

st.title("GI Reconciliation App (Simplified View)")

uploaded_file1 = st.file_uploader("Upload Atlantis File", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Upload GMI File", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    # Read data
    df1 = pd.read_csv(uploaded_file1) if uploaded_file1.name.endswith(".csv") else pd.read_excel(uploaded_file1)
    df2 = pd.read_csv(uploaded_file2) if uploaded_file2.name.endswith(".csv") else pd.read_excel(uploaded_file2)

    # Normalize expected fields
    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    # Force numeric types
    df1["QTY"] = pd.to_numeric(df1["QTY"], errors="coerce")
    df1["AMT"] = pd.to_numeric(df1["AMT"], errors="coerce")
    df2["QTY"] = pd.to_numeric(df2["QTY"], errors="coerce")
    df2["AMT"] = pd.to_numeric(df2["AMT"], errors="coerce")

    # Add source flag and unify
    df1["SOURCE"] = "ATLANTIS"
    df2["SOURCE"] = "GMI"
    df = pd.concat([df1, df2], ignore_index=True)

    # Create summary
    df["MONTH"] = pd.to_datetime(df["TRADEDATE"]).dt.to_period("M").astype(str)
    top_summary = df.groupby(["CB", "MONTH"])[["QTY", "AMT"]].sum().reset_index()

    # Display
    st.subheader("Summary")
    st.dataframe(top_summary)

    st.subheader("Detail")
    st.dataframe(df)

    # Excel export
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        top_summary.to_excel(writer, sheet_name="Summary", index=False)
        df.to_excel(writer, sheet_name="Detail", index=False)
    st.download_button("📥 Download Excel Export", output.getvalue(), file_name="recon_output.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
