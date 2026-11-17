import hashlib
import secrets
import sqlite3

connection = sqlite3.connect("database_anjay.db")
cursor1 = connection.cursor()
cursor2 = connection.cursor()
usr_tbl = "users"

# Buat tabel 'users' terlebih dahulu agar query INSERT tidak error
# cursor1.execute(f'''
#     CREATE TABLE IF NOT EXISTS {usr_tbl} (
#         username TEXT PRIMARY KEY,
#         password TEXT
#     )
# ''')
connection.commit()


class SistemLogin:
    def __init__(self):
        self.status = False

    def hashed_pass(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()  
    
    def register(self, username_input, password_input):
        salt = secrets.token_hex(16)
        pwd_hash = self.hashed_pass(password_input) + salt
        
        # PERBAIKAN 2: Nama tabel tidak boleh pakai '?', gunakan f-string
        # PERBAIKAN 3: Hanya kolom username dan password yang dimasukkan ke tabel Anda
        cursor1.execute(f"INSERT INTO {usr_tbl} (username, password, salt) VALUES (?, ?, ?)", (username_input, pwd_hash, salt))
        
        # PERBAIKAN 4: Tambahkan () pada commit()
        connection.commit()
        return f"Status : 200 | Registrasi Akun {username_input} Berhasil"

    def login(self, username_input, password_input):

        cursor2.execute(f"SELECT * FROM {usr_tbl} WHERE username = ?",(username_input,))

        data_user = cursor2.fetchone()



        if not data_user:
            return "Status: 404 | Username Tidak Ditemukan"
        else:
            db_username = data_user[1]
            db_password = data_user[2]
            salt = data_user[3]
            pwd_hash = self.hashed_pass(password_input) + salt
        
        

        if username_input == db_username and pwd_hash == db_password:
            self.status = True
            return f"Status: 200 | Login Berhasil Atas Nama {username_input}"
        else:
            return f"Status: 404 | Login Gagal Kredensial Tidak Memenuhi Syarat"
        
    def cekStatus(self):
        if self.status == True:
            return "Status: Anda Sudah Login"
        else:
            return "Status: Anda Belum Login"
    def Logout(self):
        self.status = False
        return "Anda Berhasil Logout"



# --- CARA MENJALANKAN & MENGUJI ---
akun_saya = SistemLogin()

# 1. Cek status awal (Harusnya Belum Login)
print(akun_saya.cekStatus())

# 3. Lakukan login
print(akun_saya.login('Pahri', 'Pahri123'))

# 4. Cek status setelah login (Harusnya Sudah Login)
print(akun_saya.cekStatus())

# 5. Coba Logout
print(akun_saya.Logout())

# 6. Cek status setelah logout (Harusnya Belum Login lagi)
print(akun_saya.cekStatus())