| No | Skenario | Input | Hasil Diharapkan | Hasil Aktual | Status |
|----|----------|-------|-------------------|---------------|--------|
| 1 | Login kredensial valid | admin/admin123 | Token diterbitkan | Token diterbitkan (200 OK) | Berhasil |
| 2 | Login kredensial salah | admin/salah | Akses ditolak | Error 401 "Username/password salah" | Berhasil |
| 3 | Upload file valid (.txt) | sample1.txt | File tersimpan, metadata tercatat | Tersimpan, file_id dikembalikan (201) | Berhasil |
| 4 | Upload tanpa token | GET /api/files tanpa header | Ditolak | Error 401 "Token tidak ditemukan" | Berhasil |
| 5 | Upload ekstensi terlarang | malware.exe | Ditolak | Error 400 "Tipe file tidak diizinkan" | Berhasil |
| 6 | Download file ada | file_id valid | File terunduh sama isi | File terunduh, isi identik dengan asli | Berhasil |
| 7 | Download file tidak ada | file_id palsu | Error 404 | Error 404 "File tidak ditemukan" | Berhasil |
| 8 | Hapus file | file_id valid | File & metadata terhapus | Terhapus, jumlah file berkurang 1 | Berhasil |
| 9 | Upload konkuren 10 client | 10 file paralel | Semua tersimpan, tidak ada race condition | 12/12 file tercatat lengkap di metadata | Berhasil |
| 10 | Upload file > 50MB | file 60MB (simulasi) | Ditolak | Error 413 "Ukuran file melebihi batas" | Berhasil |
