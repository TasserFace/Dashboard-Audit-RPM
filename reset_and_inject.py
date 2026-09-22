from app import app, db, User, DataRPM, ActivityLog
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random

with app.app_context():
    print("⚠️ MEMULAI HARD RESET DATABASE...")
    
    db.drop_all()
    print("✅ Seluruh tabel lama telah dihapus.")
    
    db.create_all()
    print("✅ Struktur tabel baru telah diciptakan.")

    # 1. INJEKSI USER (MENGGUNAKAN PN)
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
            password=generate_password_hash("admin"), 
            no_wa=u["wa"],
            role=u["role"]
        )
        db.session.add(baru)
    
    db.session.commit()
    print("✅ 5 User PN (Password default: admin) dan 1 Super Admin berhasil disuntikkan.")

    # 2. ALUR RELASI (MUARA APPROVAL)
    assignments = [
        {"aud": "Rayhan (Auditor/KT Hybrid)", "wa_aud": "081100000002", "kt": "Bapak Budi (KT Jakarta)", "wa_kt": "081100000001"},
        {"aud": "Deka (Auditor Jkt)", "wa_aud": "081100000003", "kt": "Bapak Budi (KT Jakarta)", "wa_kt": "081100000001"},
        {"aud": "Ani (Auditor Jateng)", "wa_aud": "081100000005", "kt": "Ibu Siti (KT Jateng)", "wa_kt": "081100000004"},
        {"aud": "Ani (Auditor Jateng)", "wa_aud": "081100000005", "kt": "Rayhan (Auditor/KT Hybrid)", "wa_kt": "081100000002"},
        {"aud": "Rayhan (Auditor/KT Hybrid)", "wa_aud": "081100000002", "kt": "Ibu Siti (KT Jateng)", "wa_kt": "081100000004"},
    ]

    unit_kerjas = ["BO Jakarta", "BO Bandung", "BO Surabaya", "Kanwil Semarang", "BO Solo", "BO Medan", "Kanwil Makassar"]
    jenis_audits = ["Reguler Audit", "Spesial Audit", "Tematik Audit", "Audit Investigasi"]
    hari_ini = date.today()

    # 3. INJEKSI 30 DATA KASUS
    for i in range(1, 31):
        assign = assignments[i % 5] # Distribusi merata ke 5 alur relasi
        unit = f"{random.choice(unit_kerjas)} {i}"
        jenis = random.choice(jenis_audits)
        
        # Skenario 1 (Kasus 1-5): Dalam Pemantauan (Auditee Aman > 14 Hari)
        if i <= 5:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 1: Auditee masih memiliki waktu panjang untuk mengumpulkan dokumen tindak lanjut.",
                tenggat_waktu=hari_ini + timedelta(days=random.randint(20, 45)),
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Dalam Pemantauan"
            )
            
        # Skenario 2 (Kasus 6-10): Dalam Pemantauan (Auditee Kritis / Telat)
        elif i <= 10:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 2: Auditee memasuki masa kritis atau sudah melewati tenggat waktu.",
                tenggat_waktu=hari_ini + timedelta(days=random.randint(-10, 10)),
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Belum Memadai"
            )
            
        # Skenario 3 (Kasus 11-15): Sedang Direviu Auditor (SLA 10 Hari Berjalan Aman)
        elif i <= 15:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 3: Dokumen diterima, Auditor sedang mereviu (Argo 10 hari berjalan aman).",
                tenggat_waktu=hari_ini + timedelta(days=30),
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Sedang Direviu Auditor",
                tgl_terima_dokumen=hari_ini - timedelta(days=random.randint(1, 5))
            )
            
        # Skenario 4 (Kasus 16-18): Sedang Direviu Auditor (SLA Auditor Jebol / Telat)
        elif i <= 18:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 4: Auditor terlambat mereviu (Sudah lebih dari 10 hari sejak auditee setor dokumen).",
                tenggat_waktu=hari_ini + timedelta(days=30),
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Sedang Direviu Auditor",
                tgl_terima_dokumen=hari_ini - timedelta(days=random.randint(12, 18))
            )
            
        # Skenario 5 (Kasus 19-22): Menunggu Approval Ketua Tim (Keputusan LHA)
        elif i <= 22:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 5: Auditor sudah memberikan keputusan LHA, saat ini sedang menunggu persetujuan Ketua Tim di Menu Approval.",
                tenggat_waktu=hari_ini + timedelta(days=15),
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Sedang Direviu Auditor",
                tgl_terima_dokumen=hari_ini - timedelta(days=2),
                status_approval="Menunggu Approval",
                usulan_status="Memadai",
                file_bukti=f"Bukti_Keputusan_{i}.pdf"
            )
            
        # Skenario 6 (Kasus 23-26): Menunggu Approval KT (KESEPAKATAN ULANG BA)
        elif i <= 26:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 6: Auditee meminta pengunduran waktu. Auditor mengusulkan perubahan tenggat waktu (Kesepakatan Ulang BA) dan menunggu Approval KT.",
                tenggat_waktu=hari_ini - timedelta(days=5), 
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Belum Memadai",
                status_approval="Menunggu Approval",
                usulan_status="Belum Memadai", # Status utama tidak berubah
                usulan_tenggat=hari_ini + timedelta(days=45), # Diundur 45 hari ke depan
                no_ba_kesepakatan=f"BA/EXT/{i:02d}/2026",
                tgl_ba_kesepakatan=hari_ini - timedelta(days=1),
                file_ba_kesepakatan=f"File_Berita_Acara_{i}.pdf"
            )
            
        # Skenario 7 (Kasus 27-30): Selesai / Memadai
        else:
            rpm = DataRPM(
                no_lha=f"LHA/2026/0{i:02d}", jenis_audit=jenis, unit_kerja=unit,
                deskripsi=f"Skenario 7: Proses tindak lanjut selesai sepenuhnya dan telah disetujui Ketua Tim.",
                tenggat_waktu=hari_ini + timedelta(days=40),
                nama_pic=f"PIC {unit}", wa_auditee=f"08990000{i:04d}",
                nama_auditor=assign['aud'], wa_auditor=assign['wa_aud'],
                nama_ketua_tim=assign['kt'], wa_ketua_tim=assign['wa_kt'],
                status="Memadai"
            )
            
        db.session.add(rpm)

    db.session.commit()
    print("✅ 30 Data Kasus RPM dengan berbagai variasi status dan BA berhasil disuntikkan.")
    print("🎉 PROSES HARD RESET SELESAI. SILAKAN LOGIN MENGGUNAKAN PN!")
