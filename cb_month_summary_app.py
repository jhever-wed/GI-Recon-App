
import streamlit as st
import pandas as pd

st.title("Test App - Excel Read Check")

uploaded_file = st.file_uploader("Upload Excel File")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.write("Excel data preview:", df.head())
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
