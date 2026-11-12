# SOPAN: Catatan Khusus & Ketentuan Operasional Perbankan BCA (NOTES)

> Dokumen komprehensif memuat aturan operasional rinci: jenis kartu paspor, asuransi jiwa Tahaka, autodebet, ketentuan TabunganKu, warkat Cek/BG Giro, spesimen tanda tangan, aturan GTU, dan 26 sandi transaksi buku tabungan.

## 1. Ketentuan Kartu Paspor BCA (Tahapan, Tahapan Gold, Tahapan Xpresi)

### A. Klasifikasi Berdasarkan Jaringan Kartu
- **Kartu Paspor GPN (Gerbang Pembayaran Nasional):**
  Digunakan khusus untuk transaksi debit di seluruh gerai berlogo Debit BCA atau GPN di Indonesia, serta tarik tunai di ATM BCA dan jaringan ATM Prima.
- **Kartu Paspor Mastercard:**
  Dapat digunakan untuk pembayaran online (e-commerce/aplikasi global), transaksi debit di jutaan gerai Debit BCA dalam negeri dan puluhan juta merchant luar negeri berlogo Mastercard, serta tarik tunai di ATM BCA, jaringan ATM Prima, dan ATM Mastercard/Cirrus di seluruh dunia.

### B. Klasifikasi Berdasarkan Tingkatan (Tier) Limit
Tersedia dalam 3 tingkatan: **Blue**, **Gold**, dan **Platinum** (masing-masing memiliki limit dan biaya administrasi berbeda).

### C. Klasifikasi Berdasarkan Percetakan Nama Nasabah
- **Non-Instan:** Nama nasabah tercetak timbul/laser di fisik kartu.
- **Instan:** Kartu langsung diberikan di cabang tanpa tercetak nama nasabah (bisa langsung digunakan).

### D. Kartu Paspor Xpresi
- Kartu Paspor Xpresi memiliki 2 opsi jaringan: **Mastercard** dan **GPN**.
- Didesain khusus generasi muda tanpa menggunakan buku tabungan fisik.

---

## 2. Ketentuan Asuransi Jiwa Tahapan Berjangka (Tahaka Reguler)

- **Fungsi Utama:** Menjamin target saldo tabungan nasabah tetap tercapai apabila nasabah meninggal dunia selama jangka waktu menabung.
- **Masa Berlaku:** Berlaku sejak tanggal pembukaan rekening sampai dengan penutupan rekening atau nasabah meninggal dunia (mana yang terjadi lebih dulu).
- **Rumus Uang Pertanggungan (UP):**
  $$\text{UP} = (n - t) \times \text{Setoran Bulanan}$$
  *Dimana $n$ adalah total tenor bulan menabung, dan $t$ adalah jumlah bulan setoran yang sudah disetorkan.*
- **Batas Maksimal Klaim Asuransi:**
  - Meninggal Dunia karena **Sakit**: Maksimal **Rp750.000.000**
  - Meninggal Dunia karena **Kecelakaan**: Maksimal **Rp1.500.000.000**
- **Ketentuan Klaim Melebihi Batas:** Jika hasil perhitungan UP berada di atas batas maksimal, maka dana yang dikembalikan ke ahli waris adalah:
  $$\text{Total Dana Kembali} = \text{Total Saldo yang Telah Ditabung} + \text{Batas Maksimal Klaim}$$

---

## 3. Ketentuan Mekanisme Autodebet Tahapan Berjangka (Tahaka)

- **Setoran Rutin Pertama:** Setoran awal akan langsung dipotong (didebet) secara otomatis dari rekening sumber dana saat sistem memproses batching di hari nasabah membuka rekening.
- **Setoran Rutin Berikutnya:** Untuk bulan-bulan selanjutnya, penarikan saldo dilakukan setiap bulan secara otomatis sesuai dengan tanggal autodebet yang ditentukan di awal.
- **Pilihan Tanggal Autodebet:** Nasabah bebas memilih tanggal autodebet antara tanggal 1 sampai maksimal tanggal 30 setiap bulannya (tanggal 31 tidak tersedia).
- **Waktu Proses:** Penarikan uang dari rekening sumber dana akan dijalankan secara otomatis oleh sistem tepat pada tanggal autodebet terpilih.
- **Penyesuaian Bulan Februari:** Khusus bulan Februari (yang tidak sampai tanggal 30), jika nasabah memilih tanggal autodebet 29 atau 30, pemotongan dana dimajukan ke tanggal 28 (atau tanggal 29 pada tahun kabisat).
- **Percobaan Ulang (Retry) Gagal Debet:** Apabila saldo di rekening sumber tidak mencukupi saat tanggal autodebet, sistem BCA akan secara otomatis mencoba memotong ulang saldo di akhir bulan berjalan.
- **Akumulasi Tunggakan:** Jika autodebet bulan berjalan tetap gagal, sistem tidak membatalkannya. Pada bulan berikutnya, sistem akan langsung memotong saldo untuk setoran bulan berjalan ditambah seluruh tunggakan bulan sebelumnya sekaligus.
- **Sanksi Penutupan Otomatis:** Apabila gagal autodebet selama 3 (tiga) bulan berturut-turut, sistem BCA akan secara otomatis menutup rekening Tahapan Berjangka tersebut.

---

## 4. Ketentuan Asuransi Jiwa Tahapan Berjangka SiMuda

- **Santunan Kematian:** Diberikan santunan duka sebesar **Rp5.000.000 per rekening**.
- **Tabel Skema Uang Pertanggungan (UP) SiMuda:**

| Masa Menabung | Penyebab Meninggal Dunia | Uang Pertanggungan (UP) |
| --- | --- | --- |
| $\le$ 1 Tahun | Sakit / Alami | Tidak mendapat klaim UP (-) |
| $\le$ 1 Tahun | Kecelakaan | $1 \times \text{UP}$, Maksimal Rp750.000.000 / nasabah |
| > 1 Tahun | Sakit / Alami | $1 \times \text{UP}$, Maksimal Rp750.000.000 / nasabah |
| > 1 Tahun | Kecelakaan | $2 \times \text{UP}$, Maksimal Rp1.500.000.000 / nasabah |

---

## 5. Karakteristik & Aturan Rekening TabunganKu

1. **Buku TabunganKu memiliki bentuk fisik, format pencatatan, dan fungsi operasional yang mirip dengan buku Tahapan BCA.:** Buku TabunganKu memiliki bentuk fisik, format pencatatan, dan fungsi operasional yang mirip dengan buku Tahapan BCA.
2. **Mendukung sistem pencatatan transaksi GTU (Gabungan Transaksi Unprinted) pada buku tabungan.:** Mendukung sistem pencatatan transaksi GTU (Gabungan Transaksi Unprinted) pada buku tabungan.
3. **Dapat digunakan untuk bertransaksi tarik, setor, dan pemindahan dana di Counter Teller cabang dan di seluruh jaringan ATM BCA.:** Dapat digunakan untuk bertransaksi tarik, setor, dan pemindahan dana di Counter Teller cabang dan di seluruh jaringan ATM BCA.
4. **Tidak dilengkapi dengan akses e-Banking (tidak bisa didaftarkan ke BCA mobile, KlikBCA, atau myBCA).:** Tidak dilengkapi dengan akses e-Banking (tidak bisa didaftarkan ke BCA mobile, KlikBCA, atau myBCA).
5. **Kartu ATM TabunganKu memiliki keterbatasan transaksi:** Kartu ATM TabunganKu memiliki keterbatasan transaksi: TIDAK DAPAT digunakan untuk belanja di mesin EDC merchant dan TIDAK DAPAT digunakan di mesin ATM bank lain (hanya khusus ATM BCA).

---

## 6. Saluran Transaksi Rekening Simpanan Pelajar (SimPel)

| Saluran Transaksi | Jenis Transaksi yang Dapat Dilakukan |
| --- | --- |
| **Counter Teller Cabang** | Setoran tunai, penarikan tunai, dan pemindahbukuan ke rekening BCA lain |
| **Mesin ATM BCA** | Cek/inquiry saldo, tarik tunai, setor tunai, transfer antar rekening BCA, dan ganti PIN |
| **Batas Belanja** | Kartu SimPel tidak dapat digunakan untuk transaksi belanja di merchant EDC |

---

## 7. Skema Perpanjangan Deposito (Deposito Berjangka & E-Deposito)

### A. Tiga Opsi Perpanjangan Deposito Berjangka (Konvensional)
- **Non-ARO (Non-Automatic Roll Over):** Deposito tidak diperpanjang saat jatuh tempo. Pokok simpanan dan bunga penempatan langsung dicairkan/ditransfer ke rekening tujuan.
- **ARO (Automatic Roll Over):** Deposito diperpanjang secara otomatis saat jatuh tempo dengan nominal pokok dan jangka waktu yang sama. Bunga penempatan ditransfer ke rekening nasabah di BCA atau bank lain.
- **ARO Plus (Automatic Roll Over Plus):** Deposito diperpanjang otomatis saat jatuh tempo dengan jangka waktu yang sama, dimana akumulasi bunga akan langsung menambah nominal pokok penempatan pada periode berikutnya.

### B. Skema Perpanjangan E-Deposito
- **ARO:** Bunga e-Deposito dikreditkan ke rekening sumber dana setiap bulan sesuai tanggal jatuh tempo.
- **ARO Plus:** Bunga e-Deposito dikreditkan pada saat jatuh tempo dan langsung dikapitalisasi menambah nominal pokok untuk periode penempatan berikutnya.
- **Catatan Otomatis:** Jika nasabah tidak mencairkan e-Deposito pada tanggal jatuh tempo, sistem akan secara otomatis memperpanjang e-Deposito dengan tenor yang sama dan suku bunga pasar yang berlaku saat itu.

---

## 8. Panduan Warkat Rekening Giro (Cek, Bilyet Giro, Letter of Authorization)

### A. Prinsip & Alur Operasional Warkat
- Cek dan Bilyet Giro (BG) disebut sebagai **warkat** yang berfungsi sebagai sarana pembayaran pengganti uang tunai.
- Setiap 1 buku Cek atau Bilyet Giro berisi **25 lembar warkat**.
- **Alur Penggunaan Buku Warkat:**
  1. **Registrasi Awal:** Sebelum warkat digunakan, buku Cek/BG wajib diregistrasi terlebih dahulu dengan menyerahkan resi pengaktifan (di halaman setelah cover) kepada Customer Service Officer (CSO) cabang.
  2. **Pemesanan Ulang:** Setelah 20 lembar warkat terpakai, pemilik rekening dapat memesan buku baru menggunakan resi permohonan di bagian belakang buku.
  3. **Pengambilan Buku Baru:** Buku warkat yang dipesan dapat diambil setelah 1 sampai 2 hari kerja.

### B. Tabel Perbandingan Cek vs Bilyet Giro vs LOA

| Parameter | Cek | Bilyet Giro (BG) | Letter of Authorization (LOA) |
| --- | --- | --- | --- |
| **Fungsi Utama** | Pencairan tunai atau pemindahbukuan (transfer) | Khusus pemindahbukuan (tidak bisa ditarik tunai) | Khusus penarikan dana rekening Giro Valas |
| **Masa Berlaku** | **250 hari** sejak tanggal penarikan | **70 hari** sejak tanggal penarikan | Sesuai instruksi transaksi |
| **Pemindahtanganan** | Dapat dipindahtangankan (endorsement) | **TIDAK** dapat dipindahtangankan | **TIDAK** dapat dipindahtangankan ke pihak ketiga |
| **Isi per Buku** | 25 lembar warkat | 25 lembar warkat | 10 lembar warkat |
| **Bea Meterai** | Sesuai ketentuan bea meterai | Sesuai ketentuan bea meterai | Wajib dibubuhi meterai Rp10.000 |
| **Pencairan Tunai** | Di seluruh kantor cabang BCA dengan identitas | Tidak bisa tunai | Di cabang pengelola rekening |

### C. Spesimen Rekening Giro
- Merupakan data digital contoh tanda tangan pemilik rekening giro (Direktur) dan pihak yang diberi kuasa (maksimal 3 orang kuasa).
- Wewenang pihak spesimen mencakup: menandatangani resi & warkat (Cek/BG), mencetak mutasi harian (bisa dikuasakan ke karyawan dengan surat kuasa), mengambil rekening koran fisik dan buku warkat baru, serta menyerahkan resi pengaktifan.

### D. Pengelolaan Rekening Koran & e-Statement Giro
- **Nasabah Badan & Perorangan:** e-Statement dikirimkan otomatis bulanan melalui email dan dapat diunduh mandiri melalui e-channel.
- **Kanal Unduh Mandiri:** KlikBCA Individu, KlikBCA Bisnis, myBCA, myBCA Bisnis, dan Ocean by BCA.
- **Status Hold / Cetak Cabang:** Cetakan fisik rekening koran hanya dicetak khusus oleh cabang asal berdasarkan pengajuan nasabah.

---

## 9. Aturan GTU (Gabungan Transaksi Unprinted) & Buku Tabungan

### A. Aturan Pencetakan GTU
Transaksi mutasi akan digabungkan menjadi baris GTU pada buku tabungan apabila:
1. Terjadi akumulasi minimal **24 transaksi** yang belum tercetak hingga tanggal 1 atau tanggal 15 setiap bulannya; ATAU
2. Terjadi akumulasi minimal **50 transaksi** dalam satu hari berjalan.
*Untuk melihat rincian transaksi GTU, nasabah dapat mengajukan cetak mutasi rekening di cabang atau melihat e-Statement di myBCA.*

### B. Anatomi Validasi Buku Tahapan
- **Kepala Buku:** Memuat nama kantor cabang asal pembukaan (misal KCP Kemang), nomor rekening (4 digit pertama menunjukkan kode cabang asal), dan nama lengkap pemilik rekening.
- **Kolom Validasi Penggantian Buku:** Memuat kode cabang tempat penggantian terakhir (misal 7720 - BC By Pass Mumbul), User-ID CS yang melayani, tanggal ganti buku, serta tanda tangan pemilik dan petugas CS.
- **Form Ganti Buku:** Terletak setelah halaman 8 buku tabungan dan wajib diisi nasabah saat penggantian buku baru.

---

## 10. Daftar Lengkap 26 Sandi Transaksi Buku Tabungan BCA

| No | Sandi | Kepanjangan / Keterangan Transaksi |
| :---: | :---: | --- |
| 1 | **ADM** | Biaya administrasi bulanan |
| 2 | **APY** | Pembayaran tagihan via ATM |
| 3 | **ATM** | Penarikan tunai lewat mesin ATM |
| 4 | **ATR** | Transfer dana / kirim uang lewat mesin ATM |
| 5 | **ATS** | Transaksi Automatic Transfer System |
| 6 | **BNG** | Kredit bunga tabungan dari bank |
| 7 | **CDM** | Setoran tunai lewat mesin Cash Deposit Machine (CDM / CRM) |
| 8 | **DBT** | Transaksi belanja menggunakan kartu debit di mesin EDC |
| 9 | **DEP** | Pencairan nominal pokok atau hasil bunga deposito |
| 10 | **GTU** | Gabungan Transaksi Unprinted (beberapa transaksi digabung karena belum cetak) |
| 11 | **HDH** | Hadiah promosi atau penalti promo dari bank |
| 12 | **ICH** | Transaksi melalui jaringan kerjasama switching antarbank |
| 13 | **IPY** | Pembayaran atau pembelian lewat Internet Banking (KlikBCA) |
| 14 | **ITA / ITR** | Transfer dana masuk/keluar lewat Internet Banking (KlikBCA) |
| 15 | **KAS** | Setor tunai atau tarik tunai langsung melalui teller cabang |
| 16 | **KL2** | Setor warkat antarbank yang membutuhkan kliring 2 hari kerja |
| 17 | **KLG** | Setor warkat dari bank lain yang diproses melalui sistem kliring |
| 18 | **KOR** | Koreksi / pembetulan atas kekeliruan pencatatan transaksi |
| 19 | **KUG** | Lalu lintas pengiriman dana melalui sarana Kiriman Uang (KU) |
| 20 | **LLG** | Transfer dana antarbank skala nasional via Sistem Kliring Nasional BI (SKNBI) |
| 21 | **MPY** | Pembayaran atau pembelian transaksi via Mobile Banking (m-BCA) |
| 22 | **MTR** | Transfer dana masuk/keluar via Mobile Banking (m-BCA) |
| 23 | **PBK** | Pemindahbukuan antar rekening di internal BCA |
| 24 | **PJK** | Pemotongan pajak penghasilan atas bunga (PPh) |
| 25 | **SWT** | Pencocokan / pelimpahan dana yang melibatkan switching antarbank |
| 26 | **TLK** | Tolakan atas warkat bank lain karena alasan tertentu |
