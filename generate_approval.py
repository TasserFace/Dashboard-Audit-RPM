from app import app, db, DataRPM
from datetime import date, timedelta
import random

# Variasi data untuk diacak
unit_kerja_list = ["BO Jakarta", "BO Bandung", "BO Surabaya", "BO Medan", "Kanwil Semarang", "BO Makassar"]
jenis_audit_list = ["Reguler Audit", "Spesial Audit", "Tematik Audit"]
auditor_list = ["Rayhan", "Budi", "Siti", "Andi"]

with app.app_context():
    print("Memulai proses pembuatan 20 data dummy KHUSUS APPROVAL...")
    
    # Kita mulai dari 51 agar nomor LHA tidak bentrok dengan 50 data sebelumnya
    for i in range(51, 71): 
        # Acak sisa hari awal
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
            # KUNCI UTAMA: Langsung set statusnya menjadi Menunggu Approval
            status_approval="Menunggu Approval" 
        )
        
        # 2. TENTUKAN SKENARIO SECARA ACAK
        skenario = random.choice(["hapus", "status_saja", "tenggat_saja", "kombinasi"])
        
        # SKENARIO A: Usulan Hapus Data (Muncul Peringatan Merah)
        if skenario == "hapus":
            dummy_rpm.usulan_status = "HAPUS"
            
        # SKENARIO B: Usulan Perubahan Status Saja (Menyertakan File Bukti)
        elif skenario == "status_saja":
            dummy_rpm.usulan_status = random.choice(["Memadai", "Belum Memadai"])
            dummy_rpm.file_bukti = f"Dummy_File_Bukti_{i}.pdf"
            
        # SKENARIO C: Usulan Perpanjangan Tenggat Waktu (Menyertakan BA)
        elif skenario == "tenggat_saja":
            dummy_rpm.usulan_status = "Dalam Pemantauan" # Status tetap
            dummy_rpm.usulan_tenggat = tenggat_awal + timedelta(days=random.randint(14, 30)) # Diperpanjang 14-30 hari
            dummy_rpm.no_ba_kesepakatan = f"BA/EXT/{i:03d}/2026"
            dummy_rpm.tgl_ba_kesepakatan = date.today()
            dummy_rpm.file_ba_kesepakatan = f"Dummy_Berita_Acara_{i}.pdf"
            
        # SKENARIO D: Kombinasi (Status Berubah & Tenggat Diperpanjang)
        elif skenario == "kombinasi":
            dummy_rpm.usulan_status = random.choice(["Memadai", "Belum Memadai"])
            dummy_rpm.file_bukti = f"Dummy_File_Bukti_{i}.pdf"
            dummy_rpm.usulan_tenggat = tenggat_awal + timedelta(days=random.randint(14, 30))
            dummy_rpm.no_ba_kesepakatan = f"BA/KMB/{i:03d}/2026"
            dummy_rpm.tgl_ba_kesepakatan = date.today()
            dummy_rpm.file_ba_kesepakatan = f"Dummy_BA_Kombinasi_{i}.pdf"
            
        db.session.add(dummy_rpm)
    
    # Simpan semua ke database
    db.session.commit()
    print("✅ SUKSES! 20 Data Dummy KHUSUS APPROVAL (berbagai skenario) berhasil disuntikkan.")
