from app import app, db, DataRPM
from datetime import date, timedelta
import random

# Variasi data untuk diacak
unit_kerja_list = [
    "BO Jakarta", "BO Bandung", "BO Surabaya", "BO Medan", 
    "BO Makassar", "Kanwil Semarang", "Kanwil Yogyakarta", 
    "BO Malang", "BO Denpasar", "BO Palembang", "BO Balikpapan"
]
jenis_audit_list = ["Reguler Audit", "Spesial Audit", "Tematik Audit", "Audit Investigasi"]
# Proporsi 'Dalam Pemantauan' diperbanyak agar dashboard lebih realistis/aktif
status_list = ["Dalam Pemantauan", "Dalam Pemantauan", "Dalam Pemantauan", "Belum Memadai", "Memadai", "Memadai"] 
auditor_list = ["Rayhan", "Budi", "Siti", "Andi", "Ratna", "Dimas"]

with app.app_context():
    print("Memulai proses pembuatan 50 data dummy RPM...")
    
    for i in range(1, 51):
        # Acak sisa hari: dari terlambat 30 hari (-30) sampai masih lama 60 hari (+60)
        # Ini akan menghasilkan data Kritis (Merah), Aman (Kuning), dan Lewat Jatuh Tempo
        sisa_hari_acak = random.randint(-30, 60)
        tenggat = date.today() + timedelta(days=sisa_hari_acak)
        
        # Buat objek data RPM baru
        dummy_rpm = DataRPM(
            no_lha=f"LHA/IA/2026/{i:03d}",
            jenis_audit=random.choice(jenis_audit_list),
            unit_kerja=random.choice(unit_kerja_list),
            deskripsi=f"Ini adalah deskripsi temuan dummy ke-{i}. Teridentifikasi adanya ketidaksesuaian prosedur operasional terkait penyaluran kredit dan administrasi pada unit kerja yang memerlukan tindak lanjut perbaikan segera sesuai rekomendasi laporan hasil audit.",
            tenggat_waktu=tenggat,
            nama_pic=f"PIC Dummy {i}",
            wa_auditee=f"08120000{i:04d}", 
            nama_auditor=random.choice(auditor_list),
            # Menggunakan nomor acak fiktif agar Fonnte tidak otomatis mengirim WA ke nomor orang tidak dikenal saat diuji coba
            wa_auditor="082100000000", 
            nama_ketua_tim="Administrator",
            wa_ketua_tim="081200000000", 
            status=random.choice(status_list)
        )
        db.session.add(dummy_rpm)
    
    # Eksekusi penyimpanan ke database
    db.session.commit()
    print("✅ SUKSES! 50 Data Dummy RPM berhasil disuntikkan ke dalam database.")
