import pandas as pd
import io
import numpy as np

def detect_header_row(file, max_rows=30, min_keyword_matches=1):
    """
    Heuristik yang lebih kuat untuk mendeteksi baris header pada file Excel/CSV.

    - Membaca sampai `max_rows` baris tanpa header.
    - Menghitung skor untuk tiap baris berdasarkan:
      * jumlah kecocokan kata kunci header
      * jumlah cell non-empty pada baris itu
      * jumlah rata-rata cell non-empty pada N baris berikutnya
    - Pilih baris dengan skor tertinggi. Namun jika skor tersebut tidak cukup
      berbeda dibanding baris 0 atau tidak punya kecocokan kata kunci minimum,
      fallback ke header=0.

    Parameter:
    - file: object file-like (memiliki .name dan readable)
    - max_rows: jumlah baris awal yang dipindai
    - min_keyword_matches: jumlah kecocokan kata kunci minimal untuk
      mempertimbangkan baris bukan baris-0

    Return: indeks baris yang dipakai sebagai header (int)
    """
    header_keywords = [
        "KODE", "KOTA", "KABUPATEN", "WILAYAH", "KECAMATAN", "DESA",
        "PEKERJAAN", "PENDIDIKAN", "SEKTOR", "JUMLAH", "TOTAL", "NO",
        "NOMOR", "TAHUN", "BULAN", "TANGGAL"
    ]

    try:
        # Baca sebagian file tanpa header
        if file.name.endswith('.csv'):
            df_temp = pd.read_csv(file, header=None, nrows=max_rows)
        else:
            df_temp = pd.read_excel(file, header=None, nrows=max_rows)
    except Exception:
        return 0

    best_idx = 0
    best_score = -1
    scores = []

    # helper untuk menghitung non-empty pada baris
    def non_empty_count(s):
        return sum(1 for v in s if pd.notna(v) and str(v).strip() != "")

    for idx, row in df_temp.iterrows():
        row_vals = [str(v).upper().strip() for v in row.values]
        kw_matches = sum(1 for v in row_vals if any(kw in v for kw in header_keywords))
        non_na = non_empty_count(row.values)

        # rata-rata non-empty pada 3 baris berikutnya (jika ada)
        next_counts = []
        for j in range(1, 4):
            if idx + j in df_temp.index:
                next_counts.append(non_empty_count(df_temp.loc[idx + j].values))
        next_avg = float(np.mean(next_counts)) if next_counts else 0.0

        # skor komposit — bobot kecil pada kecocokan kata kunci untuk prioritas
        score = kw_matches * 5.0 + non_na * 1.2 + next_avg * 0.6
        scores.append((idx, score, kw_matches, non_na, next_avg))

        if score > best_score:
            best_score = score
            best_idx = idx

    # Ambang kecocokan kata kunci
    # Jika best idx bukan 0 tapi tidak punya kecocokan minimal, pastikan skornya
    # jauh lebih baik dari baris 0 sebelum menerima; jika tidak, fallback ke 0.
    try:
        _, best_sc, best_kw, _, _ = next(s for s in scores if s[0] == best_idx)
        _, zero_sc, zero_kw, _, _ = next(s for s in scores if s[0] == 0)
    except StopIteration:
        return 0

    if best_idx == 0:
        return 0

    # cukup kata kunci?
    if best_kw < min_keyword_matches:
        # jika skor tidak jauh lebih baik dari baris 0, gunakan 0
        if best_sc < zero_sc * 1.2 + 2.0:
            return 0
    return best_idx


def _flatten_multiindex_columns(columns):
    """Flatten MultiIndex columns returned by read_* with header=[r1, r2]."""
    flat = []
    for col in columns:
        if isinstance(col, tuple):
            parts = [str(p).strip() for p in col if str(p).lower() != 'nan' and str(p).strip() != '']
            if parts:
                flat.append(' '.join(parts))
            else:
                flat.append('')
        else:
            flat.append(str(col).strip())
    return flat


def load_data(uploaded_file):
    """
    Membaca berkas CSV/Excel secara robust.

    - Mendeteksi baris header yang paling mungkin
    - Mencoba menangani header multi-baris
    - Membersihkan nama kolom (strip, gabungkan if multiindex)
    - Menghapus kolom kosong
    """
    if uploaded_file is None:
        return None

    # deteksi header
    header_row = detect_header_row(uploaded_file)

    # reset pointer sebelum membaca penuh
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    # coba baca dengan kemungkinan header multi-baris (header_row, header_row+1)
    df = None
    try:
        if uploaded_file.name.endswith('.csv'):
            # read_csv mendukung header list
            try:
                df_try = pd.read_csv(uploaded_file, header=[header_row, header_row + 1])
                # flatten cols
                df_try.columns = _flatten_multiindex_columns(df_try.columns)
                df = df_try
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, header=header_row)
        else:
            try:
                df_try = pd.read_excel(uploaded_file, header=[header_row, header_row + 1])
                df_try.columns = _flatten_multiindex_columns(df_try.columns)
                df = df_try
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file, header=header_row)
    except Exception:
        # fallback paling dasar
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, header=0)
            else:
                df = pd.read_excel(uploaded_file, header=0)
        except Exception:
            return None

    # Normalisasi nama kolom
    df.columns = [str(col).strip() for col in df.columns]

    # Jika ada kolom kosong atau bernama 'Unnamed', coba perbaiki dengan mengganti
    # header kosong/double dengan nama generik col_{i}
    new_cols = []
    seen = {}
    for i, col in enumerate(df.columns):
        name = col if col and str(col).strip() != '' else f'column_{i}'
        # hindari duplikat dengan menambahkan suffix
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0
        new_cols.append(name)
    df.columns = new_cols

    # Hapus kolom yang semuanya NaN
    df = df.dropna(axis=1, how='all')

    # Jika dataset kecil dan semua kolom bernama generik (column_0..), jangan ubah lebih jauh
    # Bersihkan spasi pada string dalam kolom kategori terpilih nanti pada pipeline

    return df
