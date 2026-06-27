"""
==============================================================
 Client CLI - Aplikasi File Sharing Sederhana
 Tugas Akhir - Client Server Programming (INF2.62.6003)
==============================================================

Client ini berkomunikasi dengan server melalui protokol HTTP
menggunakan library 'requests'. Menyediakan menu interaktif
di terminal untuk: login, upload, list, download, dan delete file.
==============================================================
"""

import os
import sys
import requests

SERVER_URL = "http://localhost:5000"


class FileShareClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.token = None
        self.username = None

    def login(self, username, password):
        resp = requests.post(
            f"{self.server_url}/api/login",
            json={"username": username, "password": password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data["token"]
            self.username = data["username"]
            print(f"[OK] Login berhasil sebagai '{self.username}'.")
            return True
        else:
            print(f"[GAGAL] {resp.json().get('error')}")
            return False

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def upload(self, filepath):
        if not os.path.exists(filepath):
            print(f"[GAGAL] File '{filepath}' tidak ditemukan di lokal.")
            return
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f)}
            resp = requests.post(
                f"{self.server_url}/api/files",
                headers=self._headers(),
                files=files,
            )
        if resp.status_code == 201:
            info = resp.json()
            print(f"[OK] Upload berhasil. file_id = {info['file_id']}")
        else:
            print(f"[GAGAL] {resp.json().get('error')}")

    def list_files(self):
        resp = requests.get(f"{self.server_url}/api/files", headers=self._headers())
        if resp.status_code != 200:
            print(f"[GAGAL] {resp.json().get('error')}")
            return
        data = resp.json()
        print(f"\nTotal file: {data['count']}")
        print("-" * 80)
        print(f"{'ID':10} {'Nama File':25} {'Ukuran':>10}  {'Diupload Oleh':12} {'Waktu'}")
        print("-" * 80)
        for f in data["files"]:
            print(f"{f['file_id'][:8]:10} {f['original_name'][:25]:25} "
                  f"{f['size_bytes']:>9}B  {f['uploaded_by']:12} {f['uploaded_at']}")
        print("-" * 80)

    def download(self, file_id_prefix, save_dir="downloads"):
        # Cari file_id lengkap berdasarkan prefix yang ditampilkan di list
        resp = requests.get(f"{self.server_url}/api/files", headers=self._headers())
        match = None
        for f in resp.json().get("files", []):
            if f["file_id"].startswith(file_id_prefix):
                match = f
                break
        if not match:
            print("[GAGAL] file_id tidak ditemukan.")
            return

        dl = requests.get(
            f"{self.server_url}/api/files/{match['file_id']}",
            headers=self._headers(),
        )
        if dl.status_code == 200:
            os.makedirs(save_dir, exist_ok=True)
            out_path = os.path.join(save_dir, match["original_name"])
            with open(out_path, "wb") as f:
                f.write(dl.content)
            print(f"[OK] File tersimpan di: {out_path}")
        else:
            print(f"[GAGAL] {dl.json().get('error')}")

    def delete(self, file_id_prefix):
        resp = requests.get(f"{self.server_url}/api/files", headers=self._headers())
        match = None
        for f in resp.json().get("files", []):
            if f["file_id"].startswith(file_id_prefix):
                match = f
                break
        if not match:
            print("[GAGAL] file_id tidak ditemukan.")
            return

        dl = requests.delete(
            f"{self.server_url}/api/files/{match['file_id']}",
            headers=self._headers(),
        )
        print(f"[{'OK' if dl.status_code == 200 else 'GAGAL'}] {dl.json().get('message', dl.json().get('error'))}")


def print_menu():
    print("""
==============================
   FILE SHARING CLIENT (CLI)
==============================
1. Upload file
2. Lihat daftar file
3. Download file
4. Hapus file
5. Keluar
""")


def main():
    client = FileShareClient(SERVER_URL)

    print("=== LOGIN ===")
    username = input("Username: ")
    password = input("Password: ")
    if not client.login(username, password):
        sys.exit(1)

    while True:
        print_menu()
        choice = input("Pilih menu: ").strip()

        if choice == "1":
            path = input("Path file yang akan diupload: ").strip()
            client.upload(path)
        elif choice == "2":
            client.list_files()
        elif choice == "3":
            fid = input("Masukkan ID file (boleh 8 karakter awal): ").strip()
            client.download(fid)
        elif choice == "4":
            fid = input("Masukkan ID file (boleh 8 karakter awal): ").strip()
            client.delete(fid)
        elif choice == "5":
            print("Keluar dari aplikasi. Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()
