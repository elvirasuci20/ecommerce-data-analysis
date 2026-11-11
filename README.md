# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Proyek akhir kelas **Belajar Analisis Data dengan Python** (Dicoding).
Analisis memakai **seluruh 9 dataset** E-Commerce Public Dataset (Olist Brazilian E-Commerce) periode **2016-2018**.

- **Nama:** Elvira Tiara Suci Tambunan
- **Email:** ds284b6x0513@student.devacademy.id
- **ID Dicoding:** ds284b6x0513

## Pertanyaan Bisnis
1. Kategori produk apa saja yang masuk Top 10 berdasarkan total revenue sepanjang 2016-2018, serta berapa rata-rata review score dan bagaimana tren revenue bulanannya, sehingga tim bisnis dapat menentukan kategori prioritas promosi dan perbaikan kualitas?
2. Di state mana pelanggan dan seller terkonsentrasi, serta berapa rata-rata waktu pengiriman dan persentase pesanan terlambat di setiap state sepanjang 2016-2018, sehingga tim logistik dapat menentukan wilayah prioritas perbaikan pengiriman?

Analisis lanjutan (tanpa machine learning): **RFM Analysis**, **Clustering dengan Binning/Manual Grouping**, dan **Geospatial Analysis**.

## Struktur Direktori
```
submission
├───dashboard
| ├───main_data.csv        # tabel gabungan 9 dataset (hasil notebook)
| ├───state_geo.csv        # titik pusat koordinat tiap state (untuk peta)
| └───dashboard.py
├───data
| ├───customers_dataset.csv
| ├───geolocation_dataset.csv
| ├───order_items_dataset.csv
| ├───order_payments_dataset.csv
| ├───order_reviews_dataset.csv
| ├───orders_dataset.csv
| ├───product_category_name_translation.csv
| ├───products_dataset.csv
| └───sellers_dataset.csv
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment
Disarankan memakai Python 3.9 atau lebih baru.

**Shell / Terminal (venv)**
```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Anaconda**
```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Menjalankan Notebook
Buka `notebook.ipynb` dengan Jupyter Notebook, VS Code, atau Google Colab. Jalankan dari folder `submission` agar path `data/` dan `dashboard/` terbaca. Notebook juga menghasilkan ulang `dashboard/main_data.csv` dan `dashboard/state_geo.csv`.

## Menjalankan Dashboard Streamlit
Dari folder `submission`:
```
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di `http://localhost:8501`. Gunakan filter pada sidebar (periode, state, kategori) untuk mengeksplorasi data.

## Dashboard Online
Tautan dashboard di Streamlit Community Cloud tertulis pada berkas `url.txt`.
Untuk deploy: unggah folder ini ke repository GitHub, buka https://share.streamlit.io, pilih repository tersebut, isi *Main file path* dengan `dashboard/dashboard.py`, lalu salin tautan hasilnya ke `url.txt`.
