import streamlit as st
import pandas as pd
from src.data_loader import load_data

st.set_page_config(
    page_title="Automated Data Visualizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Automated Enterprise Data Visualizer")
st.markdown("Unggah berkas Excel/CSV (BPS, Pemda, atau Laporan Penjualan) untuk menghasilkan dashboard otomatis.")

# Sidebar File Uploader
st.sidebar.header("📁 Ingesti Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel atau CSV", 
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
    st.sidebar.success(f"Berkas berhasil dimuat: {uploaded_file.name}")
    
    # Load data menggunakan modul pintar kita
    df = load_data(uploaded_file)
    
    if df is not None:
        st.subheader("📌 Pratinjau Data (Auto-Cleaned Header)")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Informasi Ringkas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Baris Data", len(df))
        col2.metric("Total Kolom Terdeteksi", len(df.columns))
        col3.metric("Ukuran Berkas", f"{uploaded_file.size / 1024:.1f} KB")
else:
    st.info("Silakan unggah berkas Excel/CSV melalui sidebar di sebelah kiri untuk memulai analisis.")
