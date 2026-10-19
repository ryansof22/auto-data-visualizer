import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.column_mapper import categorize_columns, get_standard_mapping, filter_regional_hierarchy
from src.visualizer import render_kpi_cards, render_primary_charts, render_category_kpis, render_data_table

st.set_page_config(
    page_title="Automated Data Visualizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Automated Enterprise Data Visualizer")
st.markdown("Unggah berkas Excel/CSV (BPS, Pemkab, Laporan Penjualan) untuk menghasilkan dashboard visualisasi otomatis terstruktur.")

st.sidebar.header("📁 Ingesti Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel atau CSV", 
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
    st.sidebar.success(f"Berkas dimuat: {uploaded_file.name}")
    
    # Stage 1: Load Data
    raw_df = load_data(uploaded_file)
    
    if raw_df is not None:
        # Stage 2: Categorization & Hierarchical Filtering
        df, dimensions, metrics = categorize_columns(raw_df)
        std_map = get_standard_mapping(dimensions)
        
        # Filter Hierarki Otomatis (Mencegah Double Counting jika ada Kode Wilayah)
        code_col = std_map.get('code') or 'KODE'
        df_filtered, filter_status = filter_regional_hierarchy(df, code_col=code_col)
        
        # Sidebar Filter Dinamis (User Manual)
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filter Data")
        
        reg_col = std_map.get('region')
        if reg_col and reg_col in df_filtered.columns:
            unique_regions = df_filtered[reg_col].dropna().unique().tolist()
            selected_region = st.sidebar.multiselect(
                f"Filter Berdasarkan {reg_col}:",
                options=unique_regions,
                default=[]
            )
            if selected_region:
                df_filtered = df_filtered[df_filtered[reg_col].isin(selected_region)]
        
        # Stage 3: Render Dashboard Visualisasi Komplit
        render_kpi_cards(df_filtered, metrics)
        render_primary_charts(df_filtered, std_map, metrics)
        
        # Rincian KPI per Kategori (Fitur Baru)
        render_category_kpis(df_filtered, std_map, metrics)
        
        # Tabel Data Terstruktur & Download
        render_data_table(df_filtered)

else:
    st.info("Silakan unggah berkas Excel/CSV melalui sidebar di sebelah kiri untuk memulai analisis.")
