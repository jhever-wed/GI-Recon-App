
import streamlit as st
import pandas as pd
import logging
import os

# Setup logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("debug_log.txt", mode='w')
    ]
)
logger = logging.getLogger()

def load_data(file):
    ext = file.name.split('.')[-1].lower()
    try:
        if ext == 'csv':
            df = pd.read_csv(file)
        elif ext in ['xls', 'xlsx']:
            df = pd.read_excel(file)
        else:
            st.error("Unsupported file type.")
            return None
        logger.debug(f"Loaded file '{file.name}' with shape {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load file '{file.name}': {e}")
        st.error(f"Failed to load {file.name}: {e}")
        return None

st.title("GI Recon App with Logging")
st.write("Upload Atlantis and GMI files to begin.")

atlantis_file = st.file_uploader("Upload Atlantis File", type=["csv", "xls", "xlsx"])
gmi_file = st.file_uploader("Upload GMI File", type=["csv", "xls", "xlsx"])

if atlantis_file and gmi_file:
    st.write("📁 Files uploaded.")
    logger.info("Both files uploaded.")

    df1 = load_data(atlantis_file)
    df2 = load_data(gmi_file)

    if df1 is None or df2 is None:
        st.stop()

    st.write("✅ Files loaded successfully.")
    logger.info("Files successfully loaded into dataframes.")
    logger.debug(f"Atlantis columns: {df1.columns.tolist()}")
    logger.debug(f"GMI columns: {df2.columns.tolist()}")

    st.write("Atlantis Columns:", df1.columns.tolist())
    st.write("GMI Columns:", df2.columns.tolist())

    # Sample processing checkpoint
    if 'RecordType' in df1.columns:
        df1 = df1[df1['RecordType'] == 'TP']
        logger.debug("Filtered Atlantis data to RecordType == 'TP'")
    else:
        st.warning("RecordType column not found in Atlantis data.")
        logger.warning("Missing 'RecordType' column in df1.")

    # Final log download
    with open("debug_log.txt", "r") as f:
        st.download_button("Download Debug Log", f, file_name="debug_log.txt")
else:
    st.info("Please upload both input files.")
