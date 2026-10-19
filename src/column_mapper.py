import pandas as pd
import numpy as np

def clean_and_coerce_types(df):
    """
    Membersihkan isi data dan mengonversi kolom angka yang terbaca sebagai teks.
    """
    df_clean = df.copy()
    
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            sample_str = df_clean[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            converted = pd.to_numeric(sample_str, errors='coerce')
            
            if converted.notna().sum() / len(df_clean) > 0.7:
                df_clean[col] = converted
                
    return df_clean

def filter_regional_hierarchy(df, code_col='KODE'):
    """
    Mencegah double counting pada data bertingkat (Kabupaten vs Kecamatan vs Desa/Dusun).
    """
    if code_col not in df.columns:
        return df, "Flat Data"
    
    # Hitung jumlah titik pada kode wilayah
    dots = df[code_col].astype(str).str.count(r'\.')
    
    # Jika ada pola kode wilayah berjenjang
    if dots.nunique() > 1:
        # Default: ambil level Kecamatan (1 titik, misal 35.16.01) agar angka tidak terhitung ganda dengan Kabupaten (0 titik)
        df_filtered = df[dots == 1].copy()
        if len(df_filtered) > 0:
            return df_filtered, "Filtered to Kecamatan Level (1 Dot)"
            
    return df, "Original Level"

def categorize_columns(df):
    """
    Memisahkan kolom menjadi Dimensi (Kategori) dan Metrik (Angka/Nilai).
    """
    df_clean = clean_and_coerce_types(df)
    
    dimensions = []
    metrics = []
    
    for col in df_clean.columns:
        col_lower = str(col).lower()
        
        if col_lower in ['no', 'nomor', 'id', 'kode']:
            dimensions.append(col)
            continue
            
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            if df_clean[col].nunique() < 5 and len(df_clean) > 20:
                dimensions.append(col)
            else:
                metrics.append(col)
        else:
            dimensions.append(col)
            
    return df_clean, dimensions, metrics

def get_standard_mapping(dimensions):
    """
    Mendeteksi peran kolom kategori utama berdasarkan kata kunci domain.
    """
    standard_map = {
        'region': None,
        'category': None,
        'time': None,
        'code': None
    }
    
    code_kw = ['kode', 'id_wilayah', 'kode_kecamatan']
    region_kw = ['wilayah', 'kecamatan', 'kabupaten', 'stasiun', 'desa', 'dusun', 'lokasi']
    category_kw = ['pekerjaan', 'pendidikan', 'sektor', 'jenis', 'kategori', 'status', 'agama']
    time_kw = ['tahun', 'bulan', 'tanggal', 'periode', 'januari', 'desember']
    
    for col in dimensions:
        col_lower = str(col).lower()
        
        if not standard_map['code'] and any(kw in col_lower for kw in code_kw):
            standard_map['code'] = col
        elif not standard_map['region'] and any(kw in col_lower for kw in region_kw):
            standard_map['region'] = col
        elif not standard_map['category'] and any(kw in col_lower for kw in category_kw):
            standard_map['category'] = col
        elif not standard_map['time'] and any(kw in col_lower for kw in time_kw):
            standard_map['time'] = col
            
    if not standard_map['category'] and len(dimensions) > 0:
        standard_map['category'] = dimensions[0]
        
    return standard_map
