import streamlit as st
import plotly.express as px
import pandas as pd

def render_kpi_cards(df, metrics):
    """
    Merender kartu KPI Global di bagian atas.
    """
    if not metrics:
        return
    
    st.subheader("📈 Indikator Global (Agregat Total)")
    cols = st.columns(min(len(metrics), 4))
    
    for i, metric in enumerate(metrics[:4]):
        total_val = df[metric].sum()
        avg_val = df[metric].mean()
        
        if total_val >= 1_000_000:
            formatted_val = f"{total_val / 1_000_000:.2f} Juta"
        elif total_val >= 1_000:
            formatted_val = f"{total_val:,.0f}".replace(",", ".")
        else:
            formatted_val = f"{total_val:.2f}"
            
        with cols[i % 4]:
            st.metric(
                label=f"Total {metric}",
                value=formatted_val,
                delta=f"Rata-rata: {avg_val:,.1f}".replace(",", ".")
            )

def render_primary_charts(df, std_map, metrics):
    """
    Merender visualisasi grafik Plotly berdasarkan skema terdeteksi.
    """
    st.markdown("---")
    st.subheader("📊 Visualisasi & Analisis Komparatif")
    
    cat_col = std_map.get('category') or std_map.get('region')
    
    if not cat_col or not metrics:
        st.warning("Data tidak memiliki kombinasi kategori dan metrik angka yang cukup untuk membuat grafik.")
        return
    
    selected_metric = metrics[0]
    if len(metrics) > 1:
        selected_metric = st.selectbox("Pilih Metrik Utama untuk Grafik:", metrics)
        
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f"**Peringkat Kategori Berdasarkan {selected_metric}**")
        df_grouped = df.groupby(cat_col)[selected_metric].sum().reset_index()
        df_grouped = df_grouped.sort_values(by=selected_metric, ascending=False).head(15)
        
        fig_bar = px.bar(
            df_grouped,
            x=selected_metric,
            y=cat_col,
            orientation='h',
            text=selected_metric,
            color=selected_metric,
            color_continuous_scale='Blues',
            labels={cat_col: "Kategori", selected_metric: "Jumlah"}
        )
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False, height=450)
        fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        st.markdown(f"**Proporsi Distribusi {selected_metric}**")
        df_top = df_grouped.head(7)
        
        fig_pie = px.pie(
            df_top,
            names=cat_col,
            values=selected_metric,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(height=450)
        st.plotly_chart(fig_pie, use_container_width=True)

def render_category_kpis(df, std_map, metrics):
    """
    Merender Indikator KPI Spesifik per Kategori/Wilayah (Sebelum Tabel Data).
    """
    st.markdown("---")
    st.subheader("📌 Rincian Indikator Kunci per Kategori (Category Breakdown)")
    
    cat_col = std_map.get('category') or std_map.get('region')
    
    if not cat_col or not metrics:
        return
        
    # Grouping per Kategori
    summary_per_cat = df.groupby(cat_col)[metrics].sum().reset_index()
    
    # Cari Kategori Tertinggi & Terrendah untuk metrik utama
    main_metric = metrics[0]
    top_cat = summary_per_cat.sort_values(by=main_metric, ascending=False).iloc[0]
    lowest_cat = summary_per_cat.sort_values(by=main_metric, ascending=True).iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"🏆 **Kategori Tertinggi ({main_metric}):**\n\n### {top_cat[cat_col]}\nNilai: **{top_cat[main_metric]:,.0f}**".replace(",", "."))
        
    with col2:
        st.warning(f"🔻 **Kategori Terrendah ({main_metric}):**\n\n### {lowest_cat[cat_col]}\nNilai: **{lowest_cat[main_metric]:,.0f}**".replace(",", "."))
        
    with col3:
        st.success(f"🔢 **Total Kategori Unik:**\n\n### {df[cat_col].nunique()} {cat_col.title()}\nMetrik Teranalisis: **{len(metrics)} Kolom**")

def render_data_table(df):
    """
    Merender tabel data interaktif beserta tombol unduh.
    """
    st.markdown("---")
    st.subheader("📋 Tabel Data Terstruktur")
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Unduh Data Bersih (CSV)",
        data=csv,
        file_name="cleaned_data.csv",
        mime="text/csv"
    )
