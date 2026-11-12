# Panduan Deploy Backend ke Vercel

Folder ini sudah dipersiapkan 100% untuk deploy ke **Vercel Serverless Functions**.

## File Konfigurasi yang Sudah Disiapkan:
1. `vercel.json`: Routing otomatis semua endpoint ke serverless function `api/index.py`.
2. `api/index.py`: Handler serverless entrypoint untuk FastAPI.
3. `knowledge/kb_index.json.gz`: Seluruh 5,608 fragmen Knowledge Base telah dikompilasi dan dikompresi menjadi 1.09 MB untuk pemuatan instan (<0.3 detik) pada cold-start Vercel.
4. `requirements.txt`: Dependensi Python yang dioptimasi khusus untuk lingkungan cloud Vercel.
5. `.vercelignore`: Mencegah upload file cache lokal, virtual environment, dan file sensitif.

---

## Cara 1: Deploy Melalui GitHub (Rekomendasi)
1. Buka terminal di folder backend ini:
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Vercel backend deploy"
   git branch -M main
   ```
2. Buat repository baru di [GitHub](https://github.com/new) (bisa public atau private).
3. Hubungkan dan push:
   ```bash
   git remote add origin https://github.com/USERNAME/NAMA_REPO.git
   git push -u origin main
   ```
4. Buka [Vercel Dashboard](https://vercel.com/new), pilih repository tersebut.
5. Masukkan **Environment Variables**:
   - `GROQ_API_KEYS`: (kunci-kunci Groq Anda, dipisahkan koma)
   - `GROQ_MODEL`: `openai/gpt-oss-20b`
   - `DEFAULT_PROVIDER`: `groq`
6. Klik tombol **Deploy**!

---

## Cara 2: Deploy Langsung via Vercel CLI (Terminal)
Jika Anda memiliki Node.js (sudah terpasang di komputer Anda):
```bash
cd backend
npx vercel
```
- Ikuti petunjuk di terminal untuk login ke akun Vercel Anda.
- Setelah berhasil, jalankan:
  ```bash
  npx vercel --prod
  ```

---

## Menghubungkan Ekstensi ke Domain Vercel:
Setelah Vercel selesai melakukan deploy, Anda akan mendapatkan URL HTTPS (contoh: `https://ping-test-server.vercel.app`).

1. Buka popup ekstensi **Ping Test (Connection Test)** di browser.
2. Pada baris **Gateway Node**, klik teks `127.0.0.1:8000`.
3. Masukkan domain Vercel Anda: `https://ping-test-server.vercel.app`.
4. Ekstensi Anda sekarang langsung terhubung ke cloud Vercel tanpa perlu menyalakan server lokal di laptop lagi!
