import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.column_mapper import categorize_columns, get_standard_mapping
from src.visualizer import render_kpi_cards, render_primary_charts, render_data_table

st.set_page_config(
    page_title="Automated Data Visualizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Automated Enterprise Data Visualizer")
st.markdown("Unggah berkas Excel/CSV untuk menghasilkan dashboard visualisasi otomatis dan terstruktur.")

# Sidebar File Uploader & Filter
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
        # Stage 2: Categorization & Mapping
        df, dimensions, metrics = categorize_columns(raw_df)
        std_map = get_standard_mapping(dimensions)
        
        # Sidebar Filter Dinamis
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filter Data")
        
        filtered_df = df.copy()
        reg_col = std_map.get('region')
        
        if reg_col and reg_col in df.columns:
            unique_regions = df[reg_col].dropna().unique().tolist()
            selected_region = st.sidebar.multiselect(
                f"Filter Berdasarkan {reg_col}:",
                options=unique_regions,
                default=[]
            )
            if selected_region:
                filtered_df = filtered_df[filtered_df[reg_col].isin(selected_region)]
        
        # Stage 3: Render Dashboard Visualisasi
        render_kpi_cards(filtered_df, metrics)
        render_primary_charts(filtered_df, std_map, metrics)
        render_data_table(filtered_df)

else:
    st.info("Silakan unggah berkas Excel/CSV melalui sidebar di sebelah kiri untuk memulai analisis.")
