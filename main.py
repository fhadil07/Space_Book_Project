import sqlite3
from datetime import datetime

DB_NAME = "space_book.db"

def inisialisasi_db():
    """Fungsi 1: Membuat database dan tabel jika belum ada"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabel User
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            no_hp TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    # 2. Tabel Fasilitas (ruangan_lapangan)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fasilitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_fasilitas TEXT,
            jenis TEXT,
            harga_per_jam INTEGER
        )
    ''')
    
    # 3. Tabel Booking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_booking TEXT UNIQUE,
            id_fasilitas INTEGER,
            id_user INTEGER,
            tanggal TEXT,
            jam_mulai TEXT,
            jam_selesai TEXT,
            status_booking TEXT,
            status_bayar TEXT,
            FOREIGN KEY(id_fasilitas) REFERENCES fasilitas(id),
            FOREIGN KEY(id_user) REFERENCES user(id)
        )
    ''')
    
    # 4. Tabel Pembayaran
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pembayaran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_booking INTEGER,
            metode TEXT,
            referensi TEXT,
            tanggal_bayar TEXT,
            FOREIGN KEY(id_booking) REFERENCES booking(id)
        )
    ''')
    
    # Seeding/Insert Data Fasilitas Awal jika masih kosong
    cursor.execute("SELECT COUNT(*) FROM fasilitas")
    if cursor.fetchone()[0] == 0:
        fasilitas_awal = [
            ('Lapangan Futsal A', 'Olahraga', 150000),
            ('Lapangan Badminton B', 'Olahraga', 75000),
            ('Ruang Meeting Alpha', 'Coworking', 60000),
            ('Ruang Meeting Beta', 'Coworking', 50000)
        ]
        cursor.executemany("INSERT INTO fasilitas (nama_fasilitas, jenis, harga_per_jam) VALUES (?, ?, ?)", fasilitas_awal)
        
    conn.commit()
    conn.close()

# Jalankan inisialisasi di awal program
inisialisasi_db()

def registrasi_user():
    """Fungsi 2: Menangani pendaftaran user baru dengan validasi"""
    print("\n=== REGISTRASI USER ===")
    nama = input("Nama Lengkap : ")
    no_hp = input("No HP        : ")
    username = input("Username     : ")
    password = input("Password     : ")
    
    # Validasi Ketentuan
    if len(no_hp) < 10:
        print("❌ ERROR: Nomor HP minimal 10 digit!")
        return
    if len(password) < 6:
        print("❌ ERROR: Password minimal 6 karakter!")
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO user (nama, no_hp, username, password) VALUES (?, ?, ?, ?)", 
                       (nama, no_hp, username, password))
        conn.commit()
        print("✅ Registrasi berhasil! Silakan login.")
    except sqlite3.IntegrityError:
        print("❌ ERROR: Username sudah digunakan, cari yang lain!")
    finally:
        conn.close()

def login_user():
    """Fungsi 3: Autentikasi user dan admin"""
    print("\n=== LOGIN SPACE-BOOK ===")
    username = input("Username : ")
    password = input("Password : ")
    
    # Hardcoded Akun Admin untuk simulasi dashboard admin
    if username == "admin" and password == "admin123":
        return {"id": 0, "nama": "Admin", "role": "admin"}
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama FROM user WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        print(f"✅ Login Berhasil! Selamat datang {user[1]}.")
        return {"id": user[0], "nama": user[1], "role": "user"}
    else:
        print("❌ Username atau Password Salah!")
        return None

def lihat_fasilitas():
    """Fungsi 4: Menampilkan daftar seluruh fasilitas yang tersedia """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama_fasilitas, jenis, harga_per_jam FROM fasilitas")
    rows = cursor.fetchall()
    conn.close()
    
    print("\n================ DAFTAR FASILITAS ================")
    print(f"{'ID':<4} | {'Nama Fasilitas':<25} | {'Jenis':<12} | {'Harga/Jam':<10}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<4} | {row[1]:<25} | {row[2]:<12} | Rp {row[3]:,}")
    print("==================================================")

def cek_jadwal_user():
    """Fungsi Tambahan: Membungkus menu cek ketersediaan jadwal secara interaktif"""
    print("\n=== CEK KETERSEDIAAN JADWAL ===")
    try:
        id_fas = int(input("Masukkan ID Fasilitas: "))
        tanggal = input("Masukkan Tanggal (DD-MM-YYYY): ")
        jam_mulai = input("Jam Mulai (HH:MM): ")
        jam_selesai = input("Jam Selesai (HH:MM): ")
        
        if cek_bentrok(id_fas, tanggal, jam_mulai, jam_selesai):
            print("\n❌ STATUS: JADWAL BENTROK / SUDAH TERISI!")
            rekomendasi_slot(id_fas, tanggal)
        else:
            print(f"\n✅ STATUS: JADWAL TERSEDIA! Silakan gunakan menu booking pada jam {jam_mulai} - {jam_selesai}.")
    except ValueError:
        print("❌ ERROR: ID Fasilitas harus berupa angka!")
            
def rekomendasi_slot(id_fasilitas, tanggal):
    """Fungsi 6: Memberikan alternatif slot kosong jika terjadi bentrok"""
    print("\n💡 Rekomendasi Slot Kosong Hari Ini:")
    jam_operasional = [f"{i:02d}:00" for i in range(8, 22)] # 08:00 sampai 21:00
    
    for i in range(len(jam_operasional) - 1):
        mulai = jam_operasional[i]
        selesai = jam_operasional[i+1]
        if not cek_bentrok(id_fasilitas, tanggal, mulai, selesai):
            print(f"   👉 {mulai} - {selesai}")

def cek_bentrok(id_fasilitas, tanggal, jam_mulai, jam_selesai):
    """Fungsi 5: Mengecek apakah ada jadwal yang bertabrakan di database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM booking 
        WHERE id_fasilitas = ? AND tanggal = ? 
        AND status_booking NOT IN ('DITOLAK', 'DIBATALKAN')
        AND (? < jam_selesai AND ? > jam_mulai)
    """
    cursor.execute(query, (id_fasilitas, tanggal, jam_mulai, jam_selesai))
    bentrok = cursor.fetchone()
    conn.close()
    return bentrok is not None

def booking_fasilitas(user_id):
    """Fungsi 7: Melakukan proses booking baru dengan kalkulasi harga yang aman"""
    lihat_fasilitas()  
    try:
        id_fasilitas = int(input("Masukkan ID Fasilitas yang ingin dibooking: "))
        tanggal = input("Masukkan Tanggal (DD-MM-YYYY): ")
        jam_mulai = input("Jam Mulai (HH:MM, contoh 08:00): ")
        jam_selesai = input("Jam Selesai (HH:MM, contoh 10:00): ")
        
        # 1. Validasi Format Jam menggunakan datetime agar aman dari salah ketik
        try:
            waktu_mulai = datetime.strptime(jam_mulai, "%H:%M")
            waktu_selesai = datetime.strptime(jam_selesai, "%H:%M")
        except ValueError:
            print("❌ ERROR: Format jam salah! Harus menggunakan format HH:MM (contoh: 08:00).")
            return
            
        # 2. Validasi agar jam selesai tidak lebih dulu dari jam mulai
        if waktu_selesai <= waktu_mulai:
            print("❌ ERROR: Jam Selesai harus lebih lambat daripada Jam Mulai!")
            return
        
        # 3. Cek Bentrok Jadwal
        if cek_bentrok(id_fasilitas, tanggal, jam_mulai, jam_selesai):
            print("\n❌ ERROR: Jadwal sudah digunakan. Silakan pilih jam lain.")
            rekomendasi_slot(id_fasilitas, tanggal)
            return
            
        # 4. Ambil data harga fasilitas dari database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT harga_per_jam, nama_fasilitas FROM fasilitas WHERE id = ?", (id_fasilitas,))
        fas = cursor.fetchone()
        
        if not fas:
            print("❌ ERROR: ID Fasilitas tidak ditemukan di database!")
            conn.close()
            return
            
        # 5. Hitung durasi nyata menggunakan selisih waktu (dalam satuan jam)
        selisih = waktu_selesai - waktu_mulai
        durasi_detik = selisih.total_seconds()
        durasi = durasi_detik / 3600  # Mengonversi detik ke jam (bisa desimal, misal 1.5 jam)
        
        # Hitung total harga pembulatan ke atas jika ada menitnya
        total_harga = int(durasi * fas[0])
        
        # 6. Generate Kode Booking otomatis
        cursor.execute("SELECT COUNT(*) FROM booking")
        count = cursor.fetchone()[0] + 1
        kode_booking = f"BK{count:04d}"
        
        # 7. Simpan Data Booking ke Database
        cursor.execute("""
            INSERT INTO booking (kode_booking, id_fasilitas, id_user, tanggal, jam_mulai, jam_selesai, status_booking, status_bayar)
            VALUES (?, ?, ?, ?, ?, ?, 'MENUNGGU PEMBAYARAN', 'BELUM LUNAS')
        """, (kode_booking, id_fasilitas, user_id, tanggal, jam_mulai, jam_selesai))
        
        conn.commit()
        
        # 8. Cetak Bukti Output (Total Harga Dijamin Muncul Disini)
        print("\n================================================")
        print("✅ BOOKING BERHASIL DICATAT!")
        print("================================================")
        print(f" Kode Booking : {kode_booking}")
        print(f" Fasilitas    : {fas[1]}")
        print(f" Tanggal      : {tanggal}")
        print(f" Jadwal Waktu : {jam_mulai} s.d {jam_selesai} ({durasi:.1f} Jam)")
        print(f" Total Harga  : Rp {total_harga:,}")
        print(f" Status Bayar : MENUNGGU PEMBAYARAN")
        print("================================================")
        print("💡 Silakan lanjut ke menu Pembayaran untuk konfirmasi transfer.")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan sistem: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
        
def proses_pembayaran(user_id):
    """Fungsi 8: Simulasi pembayaran oleh user"""
    kode_booking = input("Masukkan Kode Booking Anda: ")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, status_booking FROM booking WHERE kode_booking = ? AND id_user = ?", (kode_booking, user_id))
    booking = cursor.fetchone()
    
    if not booking:
        print("❌ Kode Booking tidak ditemukan atau bukan milik Anda.")
        conn.close()
        return
        
    print("\nPilih Metode Pembayaran:")
    print("1. Transfer Bank")
    print("2. Bayar di Tempat")
    pilihan = input("Pilih (1-2): ")
    
    if pilihan == "1":
        nama_bank = input("Nama Bank: ")
        no_ref = input("Nomor Referensi/TRF: ")
        
        cursor.execute("UPDATE booking SET status_booking = 'MENUNGGU VERIFIKASI' WHERE id = ?", (booking[0],))
        cursor.execute("INSERT INTO pembayaran (id_booking, metode, referensi, tanggal_bayar) VALUES (?, ?, ?, ?)",
                       (booking[0], f"Transfer {nama_bank}", no_ref, datetime.now().strftime("%d-%m-%Y")))
        print("✅ Bukti transfer dikirim! Menunggu verifikasi admin.")
    elif pilihan == "2":
        print("✅ Metode Bayar di tempat dipilih. Silakan lakukan pembayaran ke kasir saat datang.")
    else:
        print("❌ Pilihan tidak valid.")
        
    conn.commit()
    conn.close()

def riwayat_booking(user_id):
    """Fungsi 9: Melihat riwayat transaksi user"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.kode_booking, f.nama_fasilitas, b.tanggal, b.jam_mulai, b.jam_selesai, b.status_booking
        FROM booking b JOIN fasilitas f ON b.id_fasilitas = f.id
        WHERE b.id_user = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    print("\n================ RIWAYAT BOOKING ANDA ================")
    print(f"{'Kode':<8} | {'Fasilitas':<22} | {'Tanggal':<12} | {'Jam':<11} | {'Status':<15}")
    print("-" * 75)
    for r in rows:
        print(f"{r[0]:<8} | {r[1]:<22} | {r[2]:<12} | {r[3]}-{r[4]} | {r[5]}")
        
def dashboard_admin():
    """Fungsi 10: Menu khusus admin untuk validasi pembayaran, laporan pendapatan, dan hapus riwayat"""
    while True:
        print("\n===== DASHBOARD ADMIN =====")
        print("1. Lihat Semua Booking & Kelola Transaksi")
        print("2. Laporan Penggunaan & Pendapatan")
        print("3. Logout Admin")
        pilih = input("Pilih menu (1-3): ")
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if pilih == "1":
            cursor.execute("""
                SELECT b.id, b.kode_booking, u.nama, f.nama_fasilitas, b.status_booking 
                FROM booking b 
                JOIN user u ON b.id_user = u.id 
                JOIN fasilitas f ON b.id_fasilitas = f.id
            """)
            all_b = cursor.fetchall()
            print("\n--- DAFTAR ALL BOOKING ---")
            if not all_b:
                print("(Belum ada riwayat booking di database)")
            else:
                for b in all_b:
                    print(f"ID DB: {b[0]} | Kode: {b[1]} | User: {b[2]} | Fasilitas: {b[3]} | Status: {b[4]}")
            
            # Sub-Menu Aksi Pengelolaan Data oleh Admin
            print("\n[Aksi Kelola Data]:")
            print("1. Validasi Status Pembayaran (LUNAS/DITOLAK)")
            print("2. Hapus SALAH SATU Riwayat Booking")
            print("3. Hapus SEMUA Riwayat Booking (Reset)")
            print("4. Kembali")
            aksi = input("Pilih aksi (1-4): ")

            if aksi == "1":
                if not all_b:
                    print("❌ Tidak ada data untuk divalidasi.")
                else:
                    id_db = input("Masukkan ID DB yang ingin divalidasi: ")
                    status_baru = input("Ketik status baru (LUNAS / DITOLAK / DIBATALKAN): ").upper()
                    cursor.execute("UPDATE booking SET status_booking = ?, status_bayar = ? WHERE id = ?", 
                                   (status_baru, 'LUNAS' if status_baru == 'LUNAS' else 'BELUM LUNAS', id_db))
                    conn.commit()
                    print("✅ Status sukses diperbarui oleh Admin!")
                
            elif aksi == "2":
                if not all_b:
                    print("❌ Tidak ada data untuk dihapus.")
                else:
                    id_db = input("Masukkan ID DB riwayat yang ingin DIHAPUS: ")
                    # 1. Hapus data di tabel anak (pembayaran) terlebih dahulu agar tidak melanggar foreign key
                    cursor.execute("DELETE FROM pembayaran WHERE id_booking = ?", (id_db,))
                    # 2. Hapus data utama di tabel induk (booking)
                    cursor.execute("DELETE FROM booking WHERE id = ?", (id_db,))
                    conn.commit()
                    print(f"🗑️ Riwayat Booking dengan ID {id_db} sukses dihapus dari sistem!")

            elif aksi == "3":
                if not all_b:
                    print("❌ Database sudah dalam keadaan kosong.")
                else:
                    yakin = input("⚠️ Apakah Anda YAKIN ingin menghapus SEMUA riwayat transaksi? (y/n): ")
                    if yakin.lower() == 'y':
                        # Bersihkan kedua tabel transaksi
                        cursor.execute("DELETE FROM pembayaran")
                        cursor.execute("DELETE FROM booking")
                        conn.commit()
                        print("🗑️ Seluruh riwayat booking berhasil dibersihkan dari database!")
            
            elif aksi == "4":
                pass
                
        elif pilih == "2":
            # Menghitung Statistik dan Total Pendapatan
            cursor.execute("SELECT COUNT(*) FROM booking")
            total_b = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM booking WHERE status_booking = 'LUNAS'")
            lunas_b = cursor.fetchone()[0]
            
            # Query utama menggunakan SUM() untuk kalkulasi keuangan bersih
            query_pendapatan = """
                SELECT SUM((CAST(SUBSTR(b.jam_selesai, 1, 2) AS INT) - CAST(SUBSTR(b.jam_mulai, 1, 2) AS INT)) * f.harga_per_jam)
                FROM booking b
                JOIN fasilitas f ON b.id_fasilitas = f.id
                WHERE b.status_booking = 'LUNAS'
            """
            cursor.execute(query_pendapatan)
            total_uang = cursor.fetchone()[0]
            if total_uang is None:
                total_uang = 0
            
            print("\n================ STATISTIK LAPORAN ================")
            print(f" Total Seluruh Transaksi Booking : {total_b} Booking")
            print(f" Total Transaksi Berstatus Lunas : {lunas_b} Booking")
            print("-" * 51)
            print(f" TOTAL PENDAPATAN (LUNAS)        : Rp {total_uang:,}")
            print("===================================================")
            
        elif pilih == "3":
            print("👋 Keluar dari Dashboard Admin.")
            conn.close()
            break
        conn.close()
        
def main():
    """Fungsi Utama untuk Mengatur Jalannya Program Aplikasi"""
    user_aktif = None
    
    while True:
        if not user_aktif:
            print("\n===== WELCOME TO SPACE-BOOK =====")
            print("1. Login")
            print("2. Registrasi Akun Baru")
            print("3. Keluar Aplikasi")
            pilih = input("Pilih menu (1-3): ")
            
            if pilih == "1":
                user_aktif = login_user()
            elif pilih == "2":
                registrasi_user()
            elif pilih == "3":
                print("Terima kasih telah menggunakan SPACE-BOOK! Sampai jumpa.")
                break
            else:
                print("❌ Pilihan menu tidak tersedia.")
        else:
            # Jika yang login adalah ADMIN
            if user_aktif["role"] == "admin":
                dashboard_admin()
                user_aktif = None 
            
            # Jika yang login adalah USER biasa (Disesuaikan menjadi 6 menu sesuai Lembar Tugas)
            else:
                print(f"\n===== SPACE BOOK MENU ({user_aktif['nama']}) =====")
                print("1. Lihat Fasilitas")
                print("2. Cek Ketersediaan Jadwal")
                print("3. Booking Fasilitas")
                print("4. Riwayat Booking")
                print("5. Pembayaran")
                print("6. Logout")
                pilih = input("Pilihan Anda (1-6): ")
                
                if pilih == "1":
                    lihat_fasilitas()
                elif pilih == "2":
                    cek_jadwal_user()
                elif pilih == "3":
                    booking_fasilitas(user_aktif["id"])
                elif pilih == "4":
                    riwayat_booking(user_aktif["id"])
                elif pilih == "5":
                    proses_pembayaran(user_aktif["id"])
                elif pilih == "6":
                    print("👋 Anda berhasil logout.")
                    user_aktif = None
                else:
                    print("❌ Pilihan tidak valid.")

if __name__ == "__main__":
    main()       