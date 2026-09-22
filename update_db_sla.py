import sqlite3
import os

# Mencari lokasi brankas database Anda
BASE_DIR = '/app/data' if os.path.exists('/app/data') else os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'db_audit_v9.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    # Menambahkan kolom baru untuk mencatat SLA Auditor
    cur.execute("ALTER TABLE data_rpm ADD COLUMN tgl_terima_dokumen DATE;")
    conn.commit()
    print("✅ SUKSES BERSYUKUR! Kolom SLA Auditor (tgl_terima_dokumen) berhasil ditambahkan ke database.")
except sqlite3.OperationalError as e:
    print(f"INFO: {e}. (Ini berarti kolom sudah pernah ditambahkan, sistem aman).")
finally:
    conn.close()
