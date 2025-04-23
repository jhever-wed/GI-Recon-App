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
