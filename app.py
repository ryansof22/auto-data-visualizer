import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.column_mapper import categorize_columns, get_standard_mapping

st.set_page_config(
    page_title="Automated Data Visualizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Automated Enterprise Data Visualizer")
st.markdown("Unggah berkas Excel/CSV untuk menghasilkan pemetaan data dan dashboard otomatis.")

# Sidebar File Uploader
st.sidebar.header("📁 Ingesti Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel atau CSV", 
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
    st.sidebar.success(f"Berkas berhasil dimuat: {uploaded_file.name}")
    
    # Stage 1: Load Data
    raw_df = load_data(uploaded_file)
    
    if raw_df is not None:
        # Stage 2: Categorization & Mapping
        df, dimensions, metrics = categorize_columns(raw_df)
        std_map = get_standard_mapping(dimensions)
        
        st.subheader("📌 Pratinjau & Pemetaan Data Otomatis")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Informasi Ringkas Pemetaan Kolom
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Baris Data", len(df))
        col2.metric("Dimensi (Kategori)", len(dimensions))
        col3.metric("Metrik (Angka)", len(metrics))
        
        # Detail Hasil Deteksi Otomatis
        st.markdown("---")
        st.subheader("🎯 Hasil Deteksi Skema Data")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Hasil Identifikasi Kolom Utama:**")
            st.json({
                "Kolom Wilayah/Stasiun": std_map['region'],
                "Kolom Kategori/Pekerjaan": std_map['category'],
                "Kolom Waktu/Bulan": std_map['time']
            })
            
        with c2:
            st.markdown("**Daftar Metrik Angka yang Siap Divisualisasikan:**")
            st.write(metrics[:10] if len(metrics) > 10 else metrics)
            if len(metrics) > 10:
                st.caption(f"*Dan {len(metrics) - 10} metrik angka lainnya...")
else:
    st.info("Silakan unggah berkas Excel/CSV melalui sidebar di sebelah kiri untuk memulai analisis.")
