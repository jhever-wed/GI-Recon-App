
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Grouped Summary Comparator (v18)", layout="wide")

AGG_FUNCS = {"count": "count", "sum": "sum", "avg": "mean"}

def load_data(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file, low_memory=False)
    elif uploaded_file.name.endswith((".xls", ".xlsx")):
        return pd.read_excel(uploaded_file)
    else:
        st.error("Unsupported file format.")
        return None

def summarize(df, group_fields, numeric_fields, agg_funcs):
    summary = df.groupby(group_fields)[numeric_fields].agg(agg_funcs)
    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    return summary.sort_index()


import logging
logging.basicConfig(filename="comparison_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")


import logging
logging.basicConfig(filename="comparison_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

def log_summary_stats(df1, df2):
    logging.info(f"Atlantis summary shape: {df1.shape}")
    logging.info(f"GMI summary shape: {df2.shape}")
    logging.info(f"Shared group keys: {len(set(df1.index).intersection(df2.index))}")

def compare_summaries(df1, df2):
    log_summary_stats(df1, df2)
    diffs = []
    all_groups = sorted(set(df1.index).union(df2.index))
    for group in all_groups:
        row1 = df1.loc[group] if group in df1.index else pd.Series()
        row2 = df2.loc[group] if group in df2.index else pd.Series()
        row_diff = []
        all_cols = set(row1.index).union(row2.index)
        for col in all_cols:
            val1 = row1.get(col, "N/A")
            val2 = row2.get(col, "N/A")
            mismatch = False
            if isinstance(val1, (pd.Series, pd.DataFrame)) or isinstance(val2, (pd.Series, pd.DataFrame)):
                mismatch = True
            else:
                try:
                    mismatch = not np.isclose(val1, val2, equal_nan=True)
                except:
                    mismatch = val1 != val2
            if mismatch:
                row_diff.append((col, val1, val2))
                logging.info(f"Mismatch in group={group}, field={col}, val1={val1}, val2={val2}")
        if row_diff:
            diffs.append((group, row_diff))
    return diffs

    diffs = []
    all_groups = sorted(set(df1.index).union(df2.index))
    for group in all_groups:
        row1 = df1.loc[group] if group in df1.index else pd.Series()
        row2 = df2.loc[group] if group in df2.index else pd.Series()
        row_diff = []
        all_cols = set(row1.index).union(row2.index)
        for col in all_cols:
            val1 = row1.get(col, "N/A")
            val2 = row2.get(col, "N/A")
            mismatch = False
            if isinstance(val1, (pd.Series, pd.DataFrame)) or isinstance(val2, (pd.Series, pd.DataFrame)):
                mismatch = True
            else:
                try:
                    mismatch = not np.isclose(val1, val2, equal_nan=True)
                except:
                    mismatch = val1 != val2
            if mismatch:
                logging.info(f"Mismatch in group={group}, field={col}, val1={val1}, val2={val2}")
                row_diff.append((col, val1, val2))
        if row_diff:
            diffs.append((group, row_diff))
    return diffs

def generate_report(diffs):
    rows = []
    for group, differences in diffs:
        group_str = group if isinstance(group, str) else ', '.join(map(str, group))
        for col, val1, val2 in differences:
            rows.append({
                "Group": group_str,
                "Field": col,
                "File 1 Value": val1,
                "File 2 Value": val2
            })
    return pd.DataFrame(rows)

def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.title("📊 Grouped Summary Comparator (v18)")

# --- File uploads ---
col1, col2 = st.columns(2)
file1 = col1.file_uploader("Upload Atlantis File", type=["csv", "xlsx", "xls"])
file2 = col2.file_uploader("Upload GMI File", type=["csv", "xlsx", "xls"])

file_ytd = st.file_uploader("Optional: Upload GMI YTD File", type=["csv", "xlsx", "xls"])

if file1 and file2:
    df1 = load_data(file1)
    df2 = load_data(file2)

    if df1 is not None and df2 is not None:
        df1 = df1[df1["RecordType"] == "TR"] if "RecordType" in df1.columns else df1

        if "TradeDate" in df1.columns:
            df1["TradeDate"] = pd.to_datetime(df1["TradeDate"], format="%Y%m%d", errors="coerce")
            months1 = sorted(df1["TradeDate"].dropna().dt.to_period("M").astype(str).unique())
            selected_month_1 = st.selectbox("Select Month (Atlantis - TradeDate)", months1)
            df1 = df1[df1["TradeDate"].dt.to_period("M").astype(str) == selected_month_1]

        if "TEDATE" in df2.columns:
            df2["TEDATE"] = pd.to_datetime(df2["TEDATE"], format="%Y%m%d", errors="coerce")
            months2 = sorted(df2["TEDATE"].dropna().dt.to_period("M").astype(str).unique())
            selected_month_2 = st.selectbox("Select Month (GMI - TEDATE)", months2)
            df2 = df2[df2["TEDATE"].dt.to_period("M").astype(str) == selected_month_2]

        group1 = st.multiselect("Atlantis Grouping Fields", df1.columns)
        group2 = st.multiselect("GMI Grouping Fields", df2.columns)

        override1 = st.multiselect("Atlantis Numeric Fields", df1.columns)
        override2 = st.multiselect("GMI Numeric Fields", df2.columns)

        for col in override1:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
        for col in override2:
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        st.subheader("Field Mapping")
        mapping = {}
        for col1 in override1:
            col2 = st.selectbox(f"Map Atlantis field '{col1}' to GMI field:", override2, key=f"map_{col1}")
            mapping[col1] = col2

        agg_options = st.multiselect("Aggregations", ["count", "sum", "avg"], default=["sum", "count"])
        run_button = st.button("▶️ Run Comparison")

        if run_button and group1 and group2 and mapping and agg_options:
            agg_funcs = [AGG_FUNCS[a] for a in agg_options]
            
    # Auto-fix: skip renaming of any mapping where the source is also in group1
    safe_mapping = {k: v for k, v in mapping.items() if k not in group1}
    skipped_mappings = {k: v for k, v in mapping.items() if k in group1}
    if skipped_mappings:
        st.info(f"Skipped renaming these fields because they're used for grouping: {list(skipped_mappings.keys())}")
    df1_renamed = df1.rename(columns=safe_mapping)
    
            df2_renamed = df2.copy()
            mapped_fields = list(mapping.values())

            summary1 = summarize(df1_renamed, group1, mapped_fields, agg_funcs)
            summary2 = summarize(df2_renamed, group2, mapped_fields, agg_funcs)

            diffs = compare_summaries(summary1, summary2)
            st.divider()
            st.subheader("Comparison Results")

            if diffs:
                report_df = generate_report(diffs)
                st.dataframe(report_df, use_container_width=True)
                excel_data = to_excel_bytes(report_df)
                st.download_button("Download Comparison Report", data=excel_data, file_name="comparison.xlsx")

                with open("comparison_log.txt", "rb") as log_file:
                    st.download_button("Download Comparison Log", data=log_file.read(), file_name="comparison_log.txt")

                if file_ytd:
                    gmi_ytd = load_data(file_ytd)
                    if gmi_ytd is not None:
                        match_keys = st.multiselect("Select Key(s) to Match Against GMI YTD", [col for col in report_df.columns if col in gmi_ytd.columns])
                        if match_keys:
                            merged = pd.merge(report_df, gmi_ytd, how="left", on=match_keys, indicator=True)
                            unmatched = merged[merged["_merge"] == "left_only"]
                            final_exceptions = unmatched[report_df.columns]
                            logging.info(f"Final unmatched exceptions after GMI YTD: {len(final_exceptions)} rows")
                            st.subheader("Final Exceptions After GMI YTD")
                            st.dataframe(final_exceptions, use_container_width=True)
                            final_excel = to_excel_bytes(final_exceptions)
                            st.download_button("Download Final Exceptions", data=final_excel, file_name="final_exceptions.xlsx")
            else:
                st.success("✅ All group summaries match!")
