
import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="GI Recon", layout="wide")
st.title("📊 GI Reconciliation App")

def load_data(file):
    ext = os.path.splitext(file.name)[1].lower()
    try:
        if ext == '.csv':
            st.info("Reading CSV file...")
            return pd.read_csv(file, low_memory=False)
        elif ext in ['.xls', '.xlsx']:
            st.info("Reading Excel file with openpyxl...")
            return pd.read_excel(file, engine='openpyxl')
        else:
            st.error("Unsupported file type: " + ext)
            return None
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        return None

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is not None and df2 is not None:
        st.success("Files loaded successfully.")
        st.write("Atlantis Sample", df1.head())
        st.write("GMI Sample", df2.head())
