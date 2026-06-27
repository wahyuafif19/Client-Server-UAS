# Aplikasi File Sharing Sederhana (Client-Server)
Tugas Akhir - Client Server Programming (INF2.62.6003)
Program Studi Informatika - Universitas Negeri Padang

Replikasi fitur inti dari aplikasi Dropbox / Google Drive: upload, download,
melihat daftar file, dan menghapus file, melalui arsitektur client-server
berbasis HTTP (REST API).

## Struktur Proyek
```
filesharing/
├── server/
│   └── server.py          # Server Flask (REST API)
├── client/
│   ├── client_cli.py       # Client berbasis terminal (CLI)
│   ├── client_web.html     # Client berbasis browser (live)
│   └── client_web_demo.html# Versi statis untuk dokumentasi/screenshot
├── screenshots/            # Bukti hasil pengujian
├── testing_table.md        # Tabel hasil pengujian
└── requirements.txt
```

## Instalasi
```bash
pip install -r requirements.txt
```

## Menjalankan Server
```bash
cd server
python3 server.py
# Server berjalan di http://localhost:5000
```

## Menjalankan Client

**Opsi 1 - CLI:**
```bash
cd client
python3 client_cli.py
```
Akun demo: `admin` / `admin123` atau `user1` / `password1`

**Opsi 2 - Web:**
Buka `client/client_web.html` langsung di browser (server harus sudah berjalan).

## Endpoint API

| Method | Endpoint            | Keterangan                  | Auth |
|--------|---------------------|------------------------------|------|
| POST   | /api/login           | Login, menghasilkan token   | Tidak |
| POST   | /api/files            | Upload file                 | Ya   |
| GET    | /api/files            | Daftar semua file            | Ya   |
| GET    | /api/files/<file_id>  | Download file                | Ya   |
| DELETE | /api/files/<file_id>  | Hapus file                   | Ya   |

## Catatan Keterbatasan
- Password disimpan plain-text di kode (demo) — pada implementasi nyata wajib di-hash.
- Tidak menggunakan HTTPS/TLS (hanya HTTP biasa) — lihat slide Aspek Keamanan untuk pembahasan risikonya.
- Token tidak memiliki masa berlaku (expiry) dan hilang saat server di-restart (disimpan in-memory).
- Penyimpanan file di direktori lokal, bukan database/objek storage terdistribusi.
