import sqlite3

connection = sqlite3.connect("database_anjay.db")
cursor = connection.cursor()
cursor2 = connection.cursor()
cursor3 = connection.cursor()


class Exec:
    # Tambahkan 'self' di sini 👇
    def delete_row(self, table_name, value):
    
        cursor2.execute("SELECT * FROM users WHERE username = ?",(value,))
        data_user = cursor2.fetchone

        if not data_user:
            return "Status: 404 | Akun Tidak Ditemukan"
        else:
            cursor.execute(f"DELETE FROM {table_name} WHERE username = ?", (value,))
            connection.commit()
            return f"Berhasil Delete Username : {value}" 
    def tambah_table(self, table_name):

        cursor3.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id VARCHAR PRIMARY KEY,
            nama_barang TEXT,
            deskripsi_barang TEXT,
            harga INT)
            ''')
        return "Status: 200 | Berhasil Tambah Tabel"
        

akun = Exec()
print(akun.delete_row('users', 'Pahri'))

akun = Exec()
print(akun.tambah_table('barang'))
connection.commit()
connection.close()