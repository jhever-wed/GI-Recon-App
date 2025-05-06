
import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(layout="wide")

def load_data(file):
    try:
        ext = os.path.splitext(file.name)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file)
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(file)
        else:
            st.error("Unsupported file type.")
            return None
        st.success(f"Loaded file: {file.name}")
        return df
    except Exception as e:
        st.error(f"Failed to load {file.name}: {str(e)}")
        return None

def main():
    st.title("GI Reconciliation App")
    atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
    gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

    if atlantis_file and gmi_file:
        st.info("Reading Atlantis file...")
        df1 = load_data(atlantis_file)
        st.info("Reading GMI file...")
        df2 = load_data(gmi_file)

        if df1 is not None and df2 is not None:
            st.info("Previewing raw data:")
            st.subheader("Atlantis Sample")
            st.dataframe(df1.head())
            st.subheader("GMI Sample")
            st.dataframe(df2.head())
            st.success("Files successfully loaded and previewed. Continue implementation here.")

if __name__ == "__main__":
    main()
