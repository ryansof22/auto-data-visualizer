import pandas as pd
import numpy as np

def clean_and_coerce_types(df):
    """
    Membersihkan isi data dan mengonversi kolom angka yang terbaca sebagai teks.
    """
    df_clean = df.copy()
    
    for col in df_clean.columns:
        # Coba konversi ke numeric jika memungkinkan
        if df_clean[col].dtype == 'object':
            # Hapus spasi dan karakter khusus pemisah ribuan jika ada
            sample_str = df_clean[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            converted = pd.to_numeric(sample_str, errors='coerce')
            
            # Jika lebih dari 70% baris berhasil jadi angka, ubah tipe kolomnya
            if converted.notna().sum() / len(df_clean) > 0.7:
                df_clean[col] = converted
                
    return df_clean

def categorize_columns(df):
    """
    Memisahkan kolom menjadi Dimensi (Kategori) dan Metrik (Angka/Nilai).
    """
    df_clean = clean_and_coerce_types(df)
    
    dimensions = []
    metrics = []
    
    for col in df_clean.columns:
        col_lower = str(col).lower()
        
        # Abaikan kolom nomor urut sederhana (misal 'No', 'Kode') agar tidak dijadikan metrik utama
        if col_lower in ['no', 'nomor', 'id', 'kode']:
            dimensions.append(col)
            continue
            
        # Cek apakah kolom berupa numerik
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            # Jika angka tapi jumlah nilai uniknya sangat sedikit (misal kode status 1/0), jadikan dimensi
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
        'time': None
    }
    
    region_kw = ['wilayah', 'kecamatan', 'kabupaten', 'stasiun', 'desa', 'kota', 'lokasi']
    category_kw = ['pekerjaan', 'pendidikan', 'sektor', 'jenis', 'kategori', 'status']
    time_kw = ['tahun', 'bulan', 'tanggal', 'periode', 'januari', 'desember']
    
    for col in dimensions:
        col_lower = str(col).lower()
        
        if not standard_map['region'] and any(kw in col_lower for kw in region_kw):
            standard_map['region'] = col
        elif not standard_map['category'] and any(kw in col_lower for kw in category_kw):
            standard_map['category'] = col
        elif not standard_map['time'] and any(kw in col_lower for kw in time_kw):
            standard_map['time'] = col
            
    # Fallback default jika tidak ada kata kunci yang cocok
    if not standard_map['category'] and len(dimensions) > 0:
        standard_map['category'] = dimensions[0]
        
    return standard_map
