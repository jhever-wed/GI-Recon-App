
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Monthly Fee Reconciliation Tool", layout="wide")
st.title("📊 Monthly Fee Reconciliation Tool")

st.markdown("Upload **File A** and **File B** for matching, then optionally upload **File C** (Exception List).")

file_a = st.file_uploader("Upload File A", type=["csv", "xls", "xlsx"])
file_b = st.file_uploader("Upload File B", type=["csv", "xls", "xlsx"])
file_c = st.file_uploader("Upload File C (Exception List)", type=["csv", "xls", "xlsx"], key="file_c")

def load_file(file):
    if file.name.endswith(("xls", "xlsx")):
        return pd.read_excel(file)
    else:
        return pd.read_csv(file)

if file_a and file_b:
    df_a = load_file(file_a)
    df_b = load_file(file_b)
    
    st.subheader("1. Select Matching and Numeric Fields")
    common_cols = list(set(df_a.columns) & set(df_b.columns))
    key_cols = st.multiselect("Matching Columns (must be present in both A & B)", common_cols)
    
    numeric_cols = list(df_a.select_dtypes(include="number").columns)
    sum_cols = st.multiselect("Numeric Columns to Compare", numeric_cols)

    if st.button("Run Reconciliation") and key_cols and sum_cols:
        merged = pd.merge(df_a, df_b, on=key_cols, suffixes=("_A", "_B"), how="outer", indicator=True)
        
        def compare_sums(row):
            diffs = {}
            for col in sum_cols:
                val_a = row.get(f"{col}_A", 0)
                val_b = row.get(f"{col}_B", 0)
                diffs[col] = round(val_a - val_b, 2)
            return pd.Series(diffs)
        
        diff_df = merged.apply(compare_sums, axis=1)
        result = pd.concat([merged[key_cols + ['_merge']], diff_df], axis=1)

        st.subheader("2. Reconciliation Results")
        st.write(result)

        unmatched = result[result["_merge"] != "both"]

        if file_c:
            df_c = load_file(file_c)
            st.subheader("3. Exception Check")
            unmatched_key = unmatched[key_cols]
            exception_check = pd.merge(unmatched_key, df_c[key_cols], on=key_cols, how="left", indicator=True)
            exceptions = unmatched[exception_check["_merge"] == "left_only"]
            st.write("❌ Exceptions Not Found in File C:")
            st.write(exceptions)

        st.download_button("Download Results as CSV", result.to_csv(index=False), "reconciliation_results.csv", "text/csv")
