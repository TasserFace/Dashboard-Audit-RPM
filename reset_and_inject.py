from app import app, db, User, DataRPM, ActivityLog
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random

with app.app_context():
    print("⚠️ MEMULAI HARD RESET DATABASE...")
    
    # 1. Hapus seluruh data lama
    db.drop_all()
    print("✅ Seluruh tabel lama telah dihapus.")
    
    # 2. Buat tabel baru (dengan struktur terbaru termasuk tgl_terima_dokumen)
    db.create_all()
    print("✅ Struktur tabel baru telah diciptakan.")

    # 3. Inject User Baru
    users_data = [
        {"user": "admin", "nama": "Super Administrator", "role": "superadmin", "wa": "080000000000"},
        {"user": "00400001", "nama": "Bapak Budi (KT Jakarta)", "role": "auditor", "wa": "081100000001"},
        {"user": "00400002", "nama": "Rayhan (Auditor/KT Hybrid)", "role": "auditor", "wa": "081100000002"},
        {"user": "00400003", "nama": "Deka (Auditor Jkt)", "role": "auditor", "wa": "081100000003"},
        {"user": "00400004", "nama": "Ibu Siti (KT Jateng)", "role": "auditor", "wa": "081100000004"},
        {"user": "00400005", "nama": "Ani (Auditor Jateng)", "role": "auditor", "wa": "081100000005"},
    ]

    for u in users_data:
        baru = User(
            username=u["user"],
            nama_lengkap=u["nama"],
            password=generate_password_hash("admin"), # Semua password default adalah 'admin'
            no_wa=u["wa"],
            role=u["role"]
        )
        db.session.add(baru)
    
    db.session.commit()
    print("✅ 5 User PN (Password: admin) dan 1 Super Admin berhasil disuntikkan.")

    # 4. Inject 15 Data Kasus RPM
    hari_ini = date.today()
    
    # Skenario 1: Rayhan bertugas, lapor ke Budi (Masih Masa Auditee - Belum Ditindaklanjuti)
    for i in range(1, 4):
        rpm = DataRPM(
            no_lha=f"LHA/JKT/2026/00{i}", jenis_audit="Reguler Audit", unit_kerja=f"BO Jakarta {i}",
            deskripsi="Skenario 1: Masih dalam masa pengumpulan dokumen oleh Auditee.",
            tenggat_waktu=hari_ini + timedelta(days=random.randint(5, 12)),
            nama_pic="PIC Auditee JKT", wa_auditee="089900000001",
            nama_auditor="Rayhan (Auditor/KT Hybrid)", wa_auditor="081100000002", # Milik Rayhan
            nama_ketua_tim="Bapak Budi (KT Jakarta)", wa_ketua_tim="081100000001", # Bermuara ke Budi
            status="Dalam Pemantauan"
        )
        db.session.add(rpm)

    # Skenario 2: Deka bertugas, lapor ke Budi (Sedang Direviu Auditor - SLA 10 Hari Berjalan)
    for i in range(4, 7):
        rpm = DataRPM(
            no_lha=f"LHA/JKT/2026/00{i}", jenis_audit="Spesial Audit", unit_kerja=f"Kanwil Jakarta {i}",
            deskripsi="Skenario 2: Auditee sudah setor. Deka harus segera klik Beri Keputusan LHA sebelum SLA 10 harinya habis.",
            tenggat_waktu=hari_ini + timedelta(days=20),
            nama_pic="PIC Kanwil JKT", wa_auditee="089900000002",
            nama_auditor="Deka (Auditor Jkt)", wa_auditor="081100000003", # Milik Deka
            nama_ketua_tim="Bapak Budi (KT Jakarta)", wa_ketua_tim="081100000001", # Bermuara ke Budi
            status="Sedang Direviu Auditor",
            tgl_terima_dokumen=hari_ini - timedelta(days=random.randint(1, 8)) # Diterima beberapa hari lalu
        )
        db.session.add(rpm)

    # Skenario 3: Ani bertugas, lapor ke Ibu Siti (Auditee Telat & Auditor Telat Reviu)
    rpm_telat1 = DataRPM(
        no_lha="LHA/JTG/2026/007", jenis_audit="Tematik Audit", unit_kerja="BO Solo Baru",
        deskripsi="Skenario 3a: Auditee Telat menyerahkan dokumen.",
        tenggat_waktu=hari_ini - timedelta(days=5), # Minus 5 hari
        nama_pic="PIC BO Solo", wa_auditee="089900000003",
        nama_auditor="Ani (Auditor Jateng)", wa_auditor="081100000005", # Milik Ani
        nama_ketua_tim="Ibu Siti (KT Jateng)", wa_ketua_tim="081100000004", # Bermuara ke Siti
        status="Belum Memadai"
    )
    db.session.add(rpm_telat1)

    rpm_telat2 = DataRPM(
        no_lha="LHA/JTG/2026/008", jenis_audit="Tematik Audit", unit_kerja="Kanwil Semarang",
        deskripsi="Skenario 3b: Auditee tepat waktu, tapi Auditor (Ani) Telat mereviu lebih dari 10 hari.",
        tenggat_waktu=hari_ini + timedelta(days=30), 
        nama_pic="PIC Kanwil SMG", wa_auditee="089900000004",
        nama_auditor="Ani (Auditor Jateng)", wa_auditor="081100000005", # Milik Ani
        nama_ketua_tim="Ibu Siti (KT Jateng)", wa_ketua_tim="081100000004", # Bermuara ke Siti
        status="Sedang Direviu Auditor",
        tgl_terima_dokumen=hari_ini - timedelta(days=12) # Diterima 12 hari lalu (SLA 10 hari jebol)
    )
    db.session.add(rpm_telat2)

    # Skenario 4: Ani bertugas, lapor ke Rayhan (Hybrid Mode) - Menunggu Approval KT
    for i in range(9, 12):
        rpm = DataRPM(
            no_lha=f"LHA/HYB/2026/00{i}", jenis_audit="Audit Investigasi", unit_kerja=f"BO Tegal {i}",
            deskripsi="Skenario 4: Ani sudah mereviu, saat ini bola ada di tangan Rayhan selaku Ketua Tim untuk diapprove.",
            tenggat_waktu=hari_ini + timedelta(days=15),
            nama_pic="PIC BO Tegal", wa_auditee="089900000005",
            nama_auditor="Ani (Auditor Jateng)", wa_auditor="081100000005", # Milik Ani
            nama_ketua_tim="Rayhan (Auditor/KT Hybrid)", wa_ketua_tim="081100000002", # Bermuara ke RAYHAN
            status="Dalam Pemantauan", # Status asli
            status_approval="Menunggu Approval",
            usulan_status="Memadai", # Usulan Ani
            file_bukti="Dummy_Bukti.pdf"
        )
        db.session.add(rpm)

    # Skenario 5: Tugas Selesai (Budi dan Siti)
    for i in range(12, 16):
        rpm = DataRPM(
            no_lha=f"LHA/DONE/2026/0{i}", jenis_audit="Reguler Audit", unit_kerja=f"Kantor Pusat {i}",
            deskripsi="Skenario 5: Siklus sudah ditutup (Selesai/Memadai).",
            tenggat_waktu=hari_ini + timedelta(days=40),
            nama_pic="PIC KP", wa_auditee="089900000006",
            nama_auditor="Bapak Budi (KT Jakarta)", wa_auditor="081100000001",
            nama_ketua_tim="Ibu Siti (KT Jateng)", wa_ketua_tim="081100000004",
            status="Memadai"
        )
        db.session.add(rpm)

    db.session.commit()
    print("✅ 15 Data Kasus RPM dengan berbagai variasi status berhasil disuntikkan.")
    print("🎉 PROSES HARD RESET SELESAI. SILAKAN LOGIN DENGAN PN!")
