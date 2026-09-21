from app import app, db, DataRPM
from datetime import date, timedelta
import random

# Variasi data untuk diacak
unit_kerja_list = ["BO Jakarta", "BO Bandung", "BO Surabaya", "BO Medan", "Kanwil Semarang", "BO Makassar"]
jenis_audit_list = ["Reguler Audit", "Spesial Audit", "Tematik Audit"]
auditor_list = ["Rayhan", "Budi", "Siti", "Andi", "Ratna", "Dimas"]

with app.app_context():
    print("Memulai proses pembuatan 20 data dummy KHUSUS APPROVAL dengan variasi Tenggat Waktu...")
    
    # Kita mulai dari 71 agar tidak bentrok dengan data sebelumnya
    for i in range(71, 91): 
        # Acak sisa hari awal (hari ini)
        sisa_hari_awal = random.randint(-10, 15)
        tenggat_awal = date.today() + timedelta(days=sisa_hari_awal)
        
        # 1. BUAT DATA DASAR RPM
        dummy_rpm = DataRPM(
            no_lha=f"LHA/IA/2026/APP-{i:03d}",
            jenis_audit=random.choice(jenis_audit_list),
            unit_kerja=random.choice(unit_kerja_list),
            deskripsi=f"Temuan dummy khusus persetujuan ke-{i}. Terdapat indikasi perlunya perpanjangan waktu atau peninjauan ulang status oleh Ketua Tim Audit.",
            tenggat_waktu=tenggat_awal,
            nama_pic=f"PIC Approval {i}",
            wa_auditee=f"08120000{i:04d}", 
            nama_auditor=random.choice(auditor_list),
            wa_auditor="082100000000", 
            nama_ketua_tim="Administrator",
            wa_ketua_tim="081200000000", 
            status="Dalam Pemantauan",
            status_approval="Menunggu Approval" # KUNCI: Masuk ke tabel Approval
        )
        
        # 2. TENTUKAN 5 SKENARIO SECARA ACAK
        skenario = random.choice(["hapus", "status_saja", "tenggat_pendek", "tenggat_panjang", "kombinasi"])
        
        # Skenario 1: Hapus
        if skenario == "hapus":
            dummy_rpm.usulan_status = "HAPUS"
            # usulan_tenggat dibiarkan kosong (None)
            
        # Skenario 2: Status Saja
        elif skenario == "status_saja":
            dummy_rpm.usulan_status = random.choice(["Memadai", "Belum Memadai"])
            dummy_rpm.file_bukti = f"Dummy_Bukti_Status_{i}.pdf"
            # usulan_tenggat dibiarkan kosong (None)
            
        # Skenario 3: Perpanjangan Pendek (7 Hari)
        elif skenario == "tenggat_pendek":
            dummy_rpm.usulan_status = dummy_rpm.status # Status tetap
            dummy_rpm.usulan_tenggat = tenggat_awal + timedelta(days=7) 
            dummy_rpm.no_ba_kesepakatan = f"BA/EXT-1W/{i:03d}/2026"
            dummy_rpm.tgl_ba_kesepakatan = date.today()
            dummy_rpm.file_ba_kesepakatan = f"BA_Perpanjangan_Pendek_{i}.pdf"
            
        # Skenario 4: Perpanjangan Panjang (90 Hari)
        elif skenario == "tenggat_panjang":
            dummy_rpm.usulan_status = dummy_rpm.status # Status tetap
            dummy_rpm.usulan_tenggat = tenggat_awal + timedelta(days=90) 
            dummy_rpm.no_ba_kesepakatan = f"BA/EXT-3M/{i:03d}/2026"
            dummy_rpm.tgl_ba_kesepakatan = date.today()
            dummy_rpm.file_ba_kesepakatan = f"BA_Perpanjangan_Panjang_{i}.pdf"
            
        # Skenario 5: Kombinasi
        elif skenario == "kombinasi":
            dummy_rpm.usulan_status = "Belum Memadai"
            dummy_rpm.file_bukti = f"Dummy_Bukti_{i}.pdf"
            dummy_rpm.usulan_tenggat = tenggat_awal + timedelta(days=random.randint(14, 30))
            dummy_rpm.no_ba_kesepakatan = f"BA/KMB/{i:03d}/2026"
            dummy_rpm.tgl_ba_kesepakatan = date.today()
            dummy_rpm.file_ba_kesepakatan = f"Dummy_BA_Kombinasi_{i}.pdf"
            
        db.session.add(dummy_rpm)
    
    # Simpan ke database
    db.session.commit()
    print("✅ SUKSES! 20 Data Dummy KHUSUS APPROVAL dengan berbagai skenario waktu berhasil disuntikkan.")
