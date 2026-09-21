from app import app, db, User, DataRPM
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random

# Kumpulan 5 Akun Ketua Tim Audit (Role: ketuatim)
daftar_ketua_tim = [
    {"username": "kt01", "nama": "Bapak Budi (KT 1)", "wa": "081100000001"},
    {"username": "kt02", "nama": "Ibu Siti (KT 2)", "wa": "081100000002"},
    {"username": "kt03", "nama": "Bapak Andi (KT 3)", "wa": "081100000003"},
    {"username": "kt04", "nama": "Ibu Ratna (KT 4)", "wa": "081100000004"},
    {"username": "kt05", "nama": "Bapak Dimas (KT 5)", "wa": "081100000005"}
]

# Kumpulan 5 Akun Auditor (Role: auditor)
daftar_auditor = [
    {"username": "auditor01", "nama": "Rayhan (Auditor 1)", "wa": "082200000001"},
    {"username": "auditor02", "nama": "Ani (Auditor 2)", "wa": "082200000002"},
    {"username": "auditor03", "nama": "Rio (Auditor 3)", "wa": "082200000003"},
    {"username": "auditor04", "nama": "Maya (Auditor 4)", "wa": "082200000004"},
    {"username": "auditor05", "nama": "Deka (Auditor 5)", "wa": "082200000005"}
]

with app.app_context():
    print("Mendaftarkan 10 User (5 Ketua Tim & 5 Auditor) jika belum ada...")
    
    # 1. MASUKKAN USER KE DATABASE
    semua_user = daftar_ketua_tim + daftar_auditor
    for usr in semua_user:
        # Cek agar tidak duplikat
        if not User.query.filter_by(username=usr["username"]).first():
            role_user = 'ketuatim' if 'kt' in usr["username"] else 'auditor'
            # Semua user ini akan menggunakan password default: "password123"
            akun_baru = User(
                username=usr["username"], 
                nama_lengkap=usr["nama"], 
                no_wa=usr["wa"], 
                role=role_user, 
                password=generate_password_hash('password123')
            )
            db.session.add(akun_baru)
    db.session.commit()

    print("Membuat 20 usulan Approval yang ditujukan spesifik ke 5 Ketua Tim...")
    
    # 2. BUAT DATA RPM MENUNGGU APPROVAL (Dibagi rata ke 5 KT)
    for i in range(1, 21):
        # Memilih KT dan Auditor secara acak
        kt_terpilih = random.choice(daftar_ketua_tim)
        aud_terpilih = random.choice(daftar_auditor)
        
        dummy_rpm = DataRPM(
            no_lha=f"LHA/RAHASIA/2026/SPESIFIK-{i:03d}",
            jenis_audit="Reguler Audit",
            unit_kerja=f"Unit Kerja Dummy {i}",
            deskripsi=f"Tindak lanjut RPM nomor {i}. Pengajuan ini secara khusus ditujukan kepada {kt_terpilih['nama']}.",
            tenggat_waktu=date.today() + timedelta(days=10),
            nama_pic=f"PIC {i}",
            wa_auditee=f"0833000000{i:02d}", 
            nama_auditor=aud_terpilih["nama"],
            wa_auditor=aud_terpilih["wa"], 
            
            # KUNCI PEMISAHAN DATA:
            nama_ketua_tim=kt_terpilih["nama"],
            wa_ketua_tim=kt_terpilih["wa"], 
            
            status="Dalam Pemantauan",
            status_approval="Menunggu Approval",
            usulan_status="Memadai",
            file_bukti="Dummy_Bukti_Rahasia.pdf"
        )
        db.session.add(dummy_rpm)
    
    db.session.commit()
    print("✅ SUKSES! 10 User dan 20 Data Approval Spesifik berhasil dimasukkan.")
