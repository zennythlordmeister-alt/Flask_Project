from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import hashlib
import secrets
import sqlite3
import time

salt = secrets.token_hex(16)

app = Flask(__name__)
app.secret_key = "sckr" + salt

# --- SETUP DATABASE & TABEL PRODUK ---
connection = sqlite3.connect("database_anjay.db", check_same_thread=False)
cursor = connection.cursor()
cursor1 = connection.cursor()
cursor2 = connection.cursor()
usr_tbl = "users"
connection.row_factory = sqlite3.Row
get_data = connection.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS barang (
        id TEXT PRIMARY KEY,
        nama_barang TEXT NOT NULL,
        deskripsi_barang TEXT,
        harga INTEGER
    )
''')
connection.commit()

login_attempt = 0
max_attempt = 3
cooldown_seconds = 30

class SistemLogin:
    def __init__(self,):
        self.status = False
        self.login_attempt = login_attempt
        self.max_attempt = max_attempt

    def hashed_pass(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()  
    
    def register(self, username_input, password_input):
        try:
            if not username_input or not password_input:
                return {"Pesan": "Username dan password tidak boleh kosong!"}, 400

            salt = secrets.token_hex(16)
            pwd_hash = self.hashed_pass(password_input) + salt

            cursor1.execute(
                f"INSERT INTO {usr_tbl} (username, password, salt) VALUES (?, ?, ?)", 
                (username_input, pwd_hash, salt)
            )
            connection.commit()
            
            return {
                "Pesan": f"Registrasi Akun {username_input} Berhasil",
                "Status": 200
            }, 200

        except Exception as e:
            connection.rollback()
            return {
                "Pesan": f"Registrasi gagal: Username mungkin sudah digunakan. ({str(e)})",
                "Status": 400
            }, 400


    def login(self, username_input, password_input):
        cursor2.execute(f"SELECT * FROM {usr_tbl} WHERE username = ?", (username_input,))
        data_user = cursor2.fetchone()

        if not data_user:
            return {"Status": 404, "Pesan": "Username Tidak Ditemukan"}
        
        db_username = data_user[1]
        db_password = data_user[2]
        salt = data_user[3]
        pwd_hash = self.hashed_pass(password_input) + salt
        
        # 1. Cek apakah user sedang dalam masa cooldown (lockout)
        lockout_until = session.get('lockout_until', 0)
        now = time.time()
        
        if now < lockout_until:
            remaining_time = int(lockout_until - now)
            return {"Status": 429, "Pesan": f"Terlalu banyak percobaan. Coba lagi dalam {remaining_time} detik."}
        
        # 2. Jika Password Salah
        if username_input == db_username and pwd_hash != db_password:
            # Kurangi sisa percobaan
            self.max_attempt -= 1
            
            # Jika percobaan habis (mencapai 0 atau kurang)
            if self.max_attempt <= 0:
                cooldown_seconds = 30 # Tentukan durasi cooldown (misal 30 detik)
                session['lockout_until'] = time.time() + cooldown_seconds
                self.max_attempt = 3  # Reset kembali jatah percobaan untuk setelah cooldown
                
                return {"Status": 429, "Pesan": "Salah 3 kali! Akun dikunci sementara selama 30 detik."}
                
            self.status = False
            return {"Status": 401, "Pesan": f"Login Gagal! Sisa Percobaan {self.max_attempt}x"}
    
        # 3. Jika Password Benar
        elif username_input == db_username and pwd_hash == db_password:
            self.status = True
            # Reset jatah percobaan jika berhasil login
            self.max_attempt = 3
            session.pop('lockout_until', None)
            
            return {"Status": 200, "Pesan": f"Login Berhasil Atas Nama {username_input}"}
        
        else:
            return {"Status": 401, "Pesan": "Login Gagal Kredensial Tidak Memenuhi Syarat"}
        
            
    def cekStatus(self):
        if self.status == True:
            return {'Status': 200}
        else:
            return {'Status': 202}
    def Logout(self):
        self.status = False
        return "Anda Berhasil Logout"
    
auth = SistemLogin()

def UserBlock():
    lockout_until = session.get('lockout_until', 0)
    
    


# --- ROUTING HALAMAN UTAMA ---
@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if not data:
        return jsonify({"Pesan": "Data JSON tidak valid!"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    # Memanggil fungsi login (asumsi mengembalikan dict: {"Pesan": "...", "Status": 200})
    hasil = auth.login(username, password)
    
    # Ambil pesan dan status code langsung dari dictionary 'hasil'
    pesan = hasil.get("Pesan", "Terjadi kesalahan")
    status_code = hasil.get("Status", 500)
    
    if status_code == 200:
        # Set session user
        session['user'] = username
        
        # Kirim response JSON beserta status HTTP-nya
        return jsonify({"Pesan": pesan}), 200
    else:
        # Jika gagal (misal 401, 429, dll)
        return jsonify({"Pesan": pesan}), status_code

@app.route('/register')
def register_page():
    
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')
        
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    hasil = auth.register(username, password)
    status_code = hasil.get("Status", 200)
    return jsonify(hasil), status_code    
    

@app.route('/api/logout', methods=['POST'])
def api_logout():
    # Menghapus session user
    session.pop('user', None)
    hasil = jsonify({
        "Pesan": "Logout Berhasil!",
        "Status": 200
    }), 200
    return redirect(url_for('login_page'))

@app.route('/api/barang')
def barang():
    if 'user' in session:
        get_data.execute(f"SELECT * FROM barang")
        rows = get_data.fetchall()
        list_barang = [dict(row) for row in rows]

        return jsonify(list_barang)
    else:
        return redirect(url_for('login_page'))

@app.route('/')
def dashboard():
    
    if 'user' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login_page'))


@app.route('/gudang')
def index():
    if 'user' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login_page'))

@app.route('/tambah')
def page_tambah():
    if 'user' in session:
        return render_template('app.html')
    else:
        return redirect(url_for('login_page'))
   

# --- ENDPOINT API UNTUK MENERIMA JSON & ITERASI ---
@app.route('/api/tambah-produk', methods=['POST'])
def tambah_produk():
    # Menangkap data JSON yang dikirim dari fetch() JavaScript
    data = request.get_json()
    
    if not data:
        return jsonify({"status": 400, "pesan": "Data JSON kosong!"}), 400

    try:
        cursor.execute(
            "INSERT INTO barang (id, nama_barang, deskripsi_barang, harga_barang, stok, gambar, kategori) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data.get('id'), data.get('nama_barang'), data.get('deskripsi_barang'), data.get('harga_barang'), data.get('stok'), data.get('gambar'), data.get('kategori'))
        )
        pesan_sukses = f"Produk '{data.get('nama_barang')}' berhasil disimpan!"

        connection.commit()
        return jsonify({"status": 200, "pesan": pesan_sukses})

    except sqlite3.Error as e:
        return jsonify({"status": 500, "pesan": f"Gagal Database: {str(e)}"}), 500
    


if __name__ == '__main__':
    app.run(debug=True)