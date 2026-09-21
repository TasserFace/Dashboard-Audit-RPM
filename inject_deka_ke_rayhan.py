from app import app, db, DataRPM
from datetime import date, timedelta

with app.app_context():
    dummy_rpm = DataRPM(
        no_lha="LHA/TEST/2026/099",
        jenis_audit="Spesial Audit",
        unit_kerja="Kanwil Jakarta",
        deskripsi="Ini adalah usulan khusus dari Deka kepada Rayhan. Pastikan nomor WA Ketua Tim menggunakan nomor asli akun Rayhan agar bisa masuk ke dalam menu Approval Rayhan.",
        tenggat_waktu=date.today() + timedelta(days=10),
        nama_pic="PIC Kanwil",
        wa_auditee="0811111111", 
        nama_auditor="Deka",
        wa_auditor="082200000005", # WA Deka
        nama_ketua_tim="Rayhan",
        wa_ketua_tim="082137724982", # WA ASLI RAYHAN DI DATABASE ADMIN
        status="Dalam Pemantauan",
        status_approval="Menunggu Approval",
        usulan_status="Memadai",
        file_bukti="Bukti_Dari_Deka.pdf"
    )
    db.session.add(dummy_rpm)
    db.session.commit()
    print("✅ SUKSES! Data khusus dari Deka ke Rayhan berhasil ditambahkan.")
