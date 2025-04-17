
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Grouped Summary Comparator (with Field Mapping)", layout="wide")

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
st.title("📊 Grouped Summary Comparator (with Field Mapping)")
st.markdown("Compare two datasets by grouping and summarizing their numeric fields. Supports custom field mapping.")

col1, col2 = st.columns(2)
file1 = col1.file_uploader("Upload Atlantis File (CSV/XLSX)", type=["csv", "xlsx", "xls"])
file2 = col2.file_uploader("Upload GMI File (CSV/XLSX)", type=["csv", "xlsx", "xls"])

if file1 and file2:
    df1 = load_data(file1)
    
    df1 = df1[df1["RecordType"] == "TR"] if "RecordType" in df1.columns else df1

    st.subheader("📅 Month Filter")

    if "TradeDate" in df1.columns:
        df1["TradeDate"] = pd.to_datetime(df1["TradeDate"], errors="coerce")
        months1 = sorted(df1["TradeDate"].dropna().dt.to_period("M").astype(str).unique())
        selected_month_1 = st.selectbox("Select Month (Atlantis - based on TradeDate)", months1)
        df1 = df1[df1["TradeDate"].dt.to_period("M").astype(str) == selected_month_1]

    if "TEDATE" in df2.columns:
        df2["TEDATE"] = pd.to_datetime(df2["TEDATE"], errors="coerce")
        months2 = sorted(df2["TEDATE"].dropna().dt.to_period("M").astype(str).unique())
        selected_month_2 = st.selectbox("Select Month (GMI - based on TEDATE)", months2)
        df2 = df2[df2["TEDATE"].dt.to_period("M").astype(str) == selected_month_2]
    
    df2 = load_data(file2)

    if df1 is not None and df2 is not None:
        st.divider()
        st.subheader("🔧 Settings")

        group1 = st.multiselect("Atlantis Grouping Fields", df1.columns)
        group2 = st.multiselect("GMI Grouping Fields", df2.columns)

        override1 = st.multiselect("Atlantis Numeric Fields", df1.columns)
        override2 = st.multiselect("GMI Numeric Fields", df2.columns)

        for col in override1:
            df1[col] = pd.to_numeric(df1[col], errors='coerce')
        for col in override2:
            df2[col] = pd.to_numeric(df2[col], errors='coerce')

        st.subheader("🔁 Field Mapping")
        mapping = {}
        for col1 in override1:
            col2 = st.selectbox(f"Map Atlantis field '{col1}' to GMI field:", override2, key=f"map_{col1}")
            mapping[col1] = col2

        agg_options = st.multiselect("Aggregations", ["count", "sum", "avg"], default=["sum", "count"])
        run_button = st.button("▶️ Run Comparison")

        if run_button and group1 and group2 and mapping and agg_options:
            agg_funcs = [AGG_FUNCS[a] for a in agg_options]
            df1_renamed = df1.rename(columns=mapping)
            df2_renamed = df2.copy()
            mapped_fields = list(mapping.values())

            summary1 = summarize(df1_renamed, group1, mapped_fields, agg_funcs)
            summary2 = summarize(df2_renamed, group2, mapped_fields, agg_funcs)

            st.divider()
            st.subheader("🧪 Summary Debug Preview")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Atlantis Summary")
                st.dataframe(summary1)
            with col2:
                st.markdown("#### GMI Summary")
                st.dataframe(summary2)

            st.markdown("### 🕵️ Mismatch Diagnostics")
            missing_fields_1 = [col for col in summary2.columns if col not in summary1.columns]
            missing_fields_2 = [col for col in summary1.columns if col not in summary2.columns]
            missing_groups_1 = [idx for idx in summary2.index if idx not in summary1.index]
            missing_groups_2 = [idx for idx in summary1.index if idx not in summary2.index]

            if missing_fields_1 or missing_fields_2 or missing_groups_1 or missing_groups_2:
                if missing_fields_1:
                    st.warning(f"Fields present in GMI but missing in Atlantis: {missing_fields_1}")
                if missing_fields_2:
                    st.warning(f"Fields present in Atlantis but missing in GMI: {missing_fields_2}")
                if missing_groups_1:
                    st.info(f"Groups found in GMI but not in Atlantis: {missing_groups_1}")
                if missing_groups_2:
                    st.info(f"Groups found in Atlantis but not in GMI: {missing_groups_2}")
            else:
                st.success("✅ All summary fields and groups align!")

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
