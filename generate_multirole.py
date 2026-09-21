from app import app, db, DataRPM, User
from datetime import date, timedelta
import random

with app.app_context():
    print("Memulai proses pembuatan 10 data dummy skenario Multi-Role (Hybrid)...")
    
    # Ambil beberapa data user yang sudah ada di database untuk disesuaikan nomor WA-nya
    # Agar skenario multi-role hidup, kita ambil user dari database secara dinamis
    all_users = User.query.all()
    if not all_users:
        print("⚠️ Belum ada user di database! Jalankan setup user terlebih dahulu.")
    else:
        # Pisahkan list berdasarkan role jika ada, atau ambil acak
        auditors = [u for u in all_users if u.role in ['auditor', 'ketuatim', 'superadmin'] and u.username != 'admin']
        
        unit_kerja_list = ["BO Jakarta", "BO Bandung", "BO Surabaya", "BO Medan", "Kanwil Semarang", "BO Makassar"]
        jenis_audit_list = ["Reguler Audit", "Spesial Audit", "Tematik Audit"]
        
        for i in range(1, 11):
            # Pilih dua user secara acak dari daftar user yang ada untuk dijadikan Auditor & Ketua Tim
            auditor_user = random.choice(auditors) if auditors else None
            ketua_user = random.choice(auditors) if auditors else None
            
            # Pastikan auditor dan ketua tim tidak orang yang sama persis jika memungkinkan
            if auditor_user and ketua_user and auditor_user.id == ketua_user.id and len(auditors) > 1:
                ketua_user = random.choice([u for u in auditors if u.id != auditor_user.id])
                
            # Jika user belum ada, gunakan data cadangan string
            nama_aud = auditor_user.nama_lengkap if auditor_user else f"Auditor Multi {i}"
            wa_aud = auditor_user.no_wa if auditor_user else f"082200000{i:03d}"
            
            nama_kt = ketua_user.nama_lengkap if ketua_user else f"Ketua Tim Multi {i}"
            wa_kt = ketua_user.no_wa if ketua_user else f"081100000{i:03d}"

            # Skenario acak: Sebagian normal, sebagian meminta approval
            status_app = random.choice([None, None, "Menunggu Approval"])
            usul_stat = "Memadai" if status_app == "Menunggu Approval" else None

            sisa_hari_acak = random.randint(-5, 30)
            tenggat = date.today() + timedelta(days=sisa_hari_acak)

            dummy_rpm = DataRPM(
                no_lha=f"LHA/MULTI/2026/{i:03d}",
                jenis_audit=random.choice(jenis_audit_list),
                unit_kerja=random.choice(unit_kerja_list),
                deskripsi=f"Kasus uji coba Multi-Role ke-{i}. Di proyek ini {nama_aud} bertindak sebagai Auditor, sedangkan {nama_kt} bertindak sebagai Ketua Tim Audit.",
                tenggat_waktu=tenggat,
                nama_pic=f"PIC Unit {i}",
                wa_auditee=f"08330000{i:04d}",
                nama_auditor=nama_aud,
                wa_auditor=wa_aud,
                nama_ketua_tim=nama_kt,
                wa_ketua_tim=wa_kt,
                status="Dalam Pemantauan",
                status_approval=status_app,
                usulan_status=usul_stat,
                file_bukti="Dummy_Bukti_MultiRole.pdf" if status_app else None
            )
            db.session.add(dummy_rpm)
            
        db.session.commit()
        print("✅ SUKSES! 10 Data Kasus Multi-Role berhasil disuntikkan ke database.")
