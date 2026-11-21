from flask import Flask, render_template, request, jsonify, session, url_for, redirect, send_file
import hashlib
import secrets
import sqlite3
import pandas as pd

salt = secrets.token_hex(16)
usr_tbl = "users"

app = Flask(__name__)
app.secret_key = "sckr" + salt

connection = sqlite3.connect("database_anjay.db", check_same_thread=False)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        salt TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS barang (
        id TEXT PRIMARY KEY,
        nama_barang TEXT NOT NULL,
        deskripsi_barang TEXT,
        harga_barang INTEGER,
        stok INTEGER,
        gambar TEXT,
        kategori TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS penjualan (
        id_transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
        id_barang TEXT,
        nama_barang TEXT,
        harga_barang INTEGER,
        jumlah_beli INTEGER,
        subtotal INTEGER
    )
''')
connection.commit()


class SistemLogin:
    def hashed_pass(self, password):
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def register(self, username_input, password_input):
        salt_user = secrets.token_hex(16)
        pwd_hash = self.hashed_pass(password_input) + salt_user

        cursor.execute(
            f"INSERT INTO {usr_tbl} (username, password, salt) VALUES (?, ?, ?)",
            (username_input, pwd_hash, salt_user)
        )
        connection.commit()

        return {
            "Status": 200,
            "Pesan": f"Registrasi Akun {username_input} Berhasil"
        }

    def login(self, username_input, password_input):
        cursor.execute(f"SELECT * FROM {usr_tbl} WHERE username = ?", (username_input,))
        data_user = cursor.fetchone()

        if not data_user:
            return {"Status": 404, "Pesan": "Username Tidak Ditemukan"}

        db_username = data_user[1]
        db_password = data_user[2]
        salt_user = data_user[3]

        pwd_hash = self.hashed_pass(password_input) + salt_user

        if username_input == db_username and pwd_hash == db_password:
            return {"Status": 200, "Pesan": f"Login Berhasil Atas Nama {username_input}"}
        else:
            return {"Status": 401, "Pesan": "Username atau Password Salah!"}


auth = SistemLogin()


@app.route('/login')
def login_page():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/register')
def register_page():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')


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


@app.route('/laporan')
def page_laporan():
    if 'user' in session:
        return render_template('laporan.html')
    else:
        return redirect(url_for('login_page'))


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hasil = auth.login(username, password)
    status_code = hasil.get("Status")

    if status_code == 200:
        session['user'] = username

    return jsonify(hasil), status_code


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hasil = auth.register(username, password)
    status_code = hasil.get("Status")

    return jsonify(hasil), status_code


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))


@app.route('/api/barang')
def barang():
    if 'user' in session:
        cursor.execute("SELECT * FROM barang")
        rows = cursor.fetchall()

        list_barang = []
        for row in rows:
            list_barang.append(dict(row))

        return jsonify(list_barang)
    else:
        return redirect(url_for('login_page'))


@app.route('/api/tambah-produk', methods=['POST'])
def tambah_produk():
    data = request.get_json()

    id_barang = data.get('id').upper()
    nama_barang = data.get('nama_barang')
    deskripsi_barang = data.get('deskripsi_barang')
    harga_barang = int(data.get('harga_barang'))
    stok = int(data.get('stok'))
    gambar = data.get('gambar')
    kategori = data.get('kategori')

    data_tuple = (id_barang, nama_barang, deskripsi_barang, harga_barang, stok, gambar, kategori)

    cursor.execute(
        "INSERT INTO barang (id, nama_barang, deskripsi_barang, harga_barang, stok, gambar, kategori) VALUES (?, ?, ?, ?, ?, ?, ?)",
        data_tuple
    )
    connection.commit()

    pesan_sukses = f"Produk '{nama_barang}' berhasil disimpan!"
    return jsonify({"status": 200, "pesan": pesan_sukses})


@app.route('/api/beli', methods=['POST'])
def beli_barang():
    data = request.get_json()
    items = data.get('items')
    uang_bayar = int(data.get('uang_bayar'))

    matriks_belanja = []
    mat1 = []
    mat2 = []

    for item in items:
        id_brg = item.get('id')
        jumlah_beli = int(item.get('jumlah'))

        cursor.execute("SELECT * FROM barang WHERE id = ?", (id_brg,))
        brg_db = cursor.fetchone()

        nama_brg = brg_db['nama_barang']
        harga_brg = int(brg_db['harga_barang'])
        stok_awal = int(brg_db['stok'])

        subtotal = harga_brg * jumlah_beli

        baris_belanja = [id_brg, nama_brg, harga_brg, jumlah_beli, subtotal]
        matriks_belanja.append(baris_belanja)

        mat1.append([stok_awal])
        mat2.append([jumlah_beli])

    total_harga = 0
    total_barang = 0

    for x in range(0, len(matriks_belanja)):
        total_barang = total_barang + matriks_belanja[x][3]
        total_harga = total_harga + matriks_belanja[x][4]

    if total_barang >= 3:
        potongan = int(total_harga * 0.1)
    else:
        potongan = 0

    total_bayar = total_harga - potongan
    uang_kembali = uang_bayar - total_bayar

    if uang_bayar < total_bayar:
        return jsonify({
            "status": 400,
            "pesan": f"Uang bayar kurang! Total yang harus dibayar adalah Rp {total_bayar}"
        }), 400

    mat_sisa_stok = []

    for x in range(0, len(mat1)):
        row = []
        for y in range(0, len(mat1[0])):
            sisa = mat1[x][y] - mat2[x][y]
            row.append(sisa)
        mat_sisa_stok.append(row)

    for x in range(0, len(matriks_belanja)):
        id_target = matriks_belanja[x][0]
        nama_target = matriks_belanja[x][1]
        harga_target = matriks_belanja[x][2]
        jumlah_target = matriks_belanja[x][3]
        sub_target = matriks_belanja[x][4]
        stok_baru = mat_sisa_stok[x][0]

        cursor.execute("UPDATE barang SET stok = ? WHERE id = ?", (stok_baru, id_target))
        cursor.execute(
            "INSERT INTO penjualan (id_barang, nama_barang, harga_barang, jumlah_beli, subtotal) VALUES (?, ?, ?, ?, ?)",
            (id_target, nama_target, harga_target, jumlah_target, sub_target)
        )

    connection.commit()

    return jsonify({
        "status": 200,
        "pesan": "Transaksi Pembelian Berhasil!",
        "matriks_belanja": matriks_belanja,
        "mat_stok_awal": mat1,
        "mat_jumlah_beli": mat2,
        "mat_sisa_stok": mat_sisa_stok,
        "total_barang": total_barang,
        "total_harga": total_harga,
        "potongan": potongan,
        "total_bayar": total_bayar,
        "uang_bayar": uang_bayar,
        "uang_kembali": uang_kembali
    })


def buat_dataframe_laporan():
    cursor.execute("SELECT * FROM penjualan")
    rows = cursor.fetchall()

    list_no = []
    list_id = []
    list_nama = []
    list_harga = []
    list_jumlah = []
    list_total = []

    ulang = len(rows)
    for i in range(ulang):
        list_no.append(i + 1)
        list_id.append(rows[i]['id_barang'])
        list_nama.append(rows[i]['nama_barang'])
        list_harga.append(rows[i]['harga_barang'])
        list_jumlah.append(rows[i]['jumlah_beli'])
        list_total.append(rows[i]['subtotal'])

    data_laporan = {
        "No": list_no,
        "ID Barang": list_id,
        "Nama Barang": list_nama,
        "Harga Satuan": list_harga,
        "Jumlah Terjual": list_jumlah,
        "Total Harga": list_total
    }

    df_laporan = pd.DataFrame(data_laporan)
    return df_laporan


@app.route('/api/laporan')
def api_laporan():
    if 'user' in session:
        df_laporan = buat_dataframe_laporan()

        if len(df_laporan) > 0:
            total_terjual = int(df_laporan["Jumlah Terjual"].sum())
            total_pendapatan = int(df_laporan["Total Harga"].sum())
        else:
            total_terjual = 0
            total_pendapatan = 0

        return jsonify({
            "total_transaksi": len(df_laporan),
            "total_terjual": total_terjual,
            "total_pendapatan": total_pendapatan,
            "tabel_dataframe": df_laporan.to_dict(orient="records")
        })
    else:
        return redirect(url_for('login_page'))


@app.route('/api/export-excel')
def export_excel():
    if 'user' in session:
        df_laporan = buat_dataframe_laporan()

        nama_file = "Laporan_Penjualan_Toko.xlsx"
        df_laporan.to_excel(nama_file, index=False)

        return send_file(nama_file, as_attachment=True)
    else:
        return redirect(url_for('login_page'))


if __name__ == '__main__':
    app.run(debug=True, port=5002)
