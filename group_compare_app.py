
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Grouped Summary Comparator (Debug Mode)", layout="wide")

AGG_FUNCS = {
    "count": "count",
    "sum": "sum",
    "avg": "mean"
}

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

def compare_summaries(df1, df2):
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
            if pd.isna(val1) and pd.isna(val2):
                continue
            try:
                if round(val1, 5) == round(val2, 5):
                    continue
            except:
                pass
            if val1 != val2:
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

# --- UI ---
st.title("📊 Grouped Summary Comparator (Debug Mode)")
st.markdown("Compare two datasets by grouping and summarizing their numeric fields.")

col1, col2 = st.columns(2)
file1 = col1.file_uploader("Upload File 1 (CSV/XLSX)", type=["csv", "xlsx", "xls"])
file2 = col2.file_uploader("Upload File 2 (CSV/XLSX)", type=["csv", "xlsx", "xls"])

if file1 and file2:
    df1 = load_data(file1)
    df2 = load_data(file2)

    if df1 is not None and df2 is not None:
        st.divider()
        st.subheader("🔧 Settings")

        group1 = st.multiselect("Grouping Fields (File 1)", df1.columns)
        group2 = st.multiselect("Grouping Fields (File 2)", df2.columns)

        column_override1 = st.multiselect("Columns to treat as numeric (File 1)", df1.columns)
        column_override2 = st.multiselect("Columns to treat as numeric (File 2)", df2.columns)

        debug1 = {}
        debug2 = {}

        for col in column_override1:
            try:
                df1[col] = pd.to_numeric(df1[col], errors='coerce')
            except:
                pass
            debug1[col] = str(df1[col].dtype)

        for col in column_override2:
            try:
                df2[col] = pd.to_numeric(df2[col], errors='coerce')
            except:
                pass
            debug2[col] = str(df2[col].dtype)

        all_fields = sorted(set(column_override1 + column_override2))
        fields = st.multiselect("Numeric Fields to Summarize", all_fields, default=all_fields)

        with st.expander("🔍 Debug Info"):
            st.write("File 1 column types:")
            st.json(debug1)
            st.write("File 2 column types:")
            st.json(debug2)

        agg_options = st.multiselect("Aggregations", ["count", "sum", "avg"], default=["sum", "count"])
        run_button = st.button("▶️ Run Comparison")

        if run_button and fields and agg_options and group1 and group2:
            agg_funcs = [AGG_FUNCS[a] for a in agg_options]

            summary1 = summarize(df1, group1, fields, agg_funcs)
            summary2 = summarize(df2, group2, fields, agg_funcs)

            st.divider()
            st.subheader("📈 Summary Comparison Results")
            diffs = compare_summaries(summary1, summary2)

            if diffs:
                report_df = generate_report(diffs)
                st.warning(f"Found mismatches in {len(diffs)} groups.")
                st.dataframe(report_df, use_container_width=True)

                excel_data = to_excel_bytes(report_df)
                st.download_button("📥 Download Report as Excel", data=excel_data,
                                   file_name="summary_comparison_report.xlsx", mime="application/vnd.ms-excel")
            else:
                st.success("✅ All group summaries match exactly!")
