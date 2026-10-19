import pandas as pd
import io

def detect_header_row(file, max_rows=20, min_matches=2):
    """
    Memindai N baris pertama file Excel/CSV untuk menentukan 
    baris mana yang berisi nama kolom (header) asli.

    - max_rows: berapa banyak baris awal yang akan dipindai
    - min_matches: minimal jumlah "kata kunci header" yang harus cocok
      pada sebuah baris agar dianggap sebagai header. Jika tidak tercapai,
      fungsi akan mengembalikan 0 (anggap baris pertama sebagai header).
    """
    # Kata kunci umum yang biasa muncul di baris header
    header_keywords = [
        "KODE", "WILAYAH", "KECAMATAN", "PEKERJAAN", "PENDIDIKAN", 
        "STASIUN", "JANUARI", "NO", "NOMOR", "JUMLAH", "TOTAL"
    ]
    
    try:
        # BACA SEMENTARA TANPA HEADER
        if file.name.endswith('.csv'):
            df_temp = pd.read_csv(file, header=None, nrows=max_rows)
        else:
            df_temp = pd.read_excel(file, header=None, nrows=max_rows)
            
        header_idx = 0
        max_matches = 0
        
        # Cek baris demi baris mana yang paling banyak memiliki kata kunci header
        for idx, row in df_temp.iterrows():
            row_values = [str(val).upper().strip() for val in row.values if pd.notna(val)]
            matches = sum(1 for val in row_values if any(kw in val for kw in header_keywords))
            
            if matches > max_matches:
                max_matches = matches
                header_idx = idx
                
        # Jika tidak ada baris yang mencapai ambang min_matches, kembalikan 0
        if max_matches < min_matches:
            return 0
        return header_idx
    except Exception:
        return 0


def load_data(uploaded_file):
    """
    Membaca berkas CSV/Excel berdasarkan baris header yang telah terdeteksi.
    """
    if uploaded_file is None:
        return None
    
    header_row = detect_header_row(uploaded_file)
    try:
        uploaded_file.seek(0) # Reset pointer file
    except Exception:
        pass
    
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, header=header_row)
    else:
        # Jika file Excel, baca sheet pertama
        df = pd.read_excel(uploaded_file, header=header_row)
        
    # Bersihkan nama kolom dari spasi berlebih
    df.columns = [str(col).strip() for col in df.columns]
    
    # Hapus kolom yang semuanya bernilai NaN atau 'Unnamed' tak berguna
    df = df.dropna(how='all', axis=1)
    
    return df
