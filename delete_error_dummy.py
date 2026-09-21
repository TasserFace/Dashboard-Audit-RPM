from app import app, db, DataRPM

with app.app_context():
    print("Mencari 20 data dummy awal yang error (APP-051 s.d APP-070)...")
    
    # Membuat daftar target LHA yang akan dihapus secara spesifik
    lha_target = [f"LHA/IA/2026/APP-{i:03d}" for i in range(51, 71)]
    
    # Menarik data dari database yang cocok dengan target LHA
    data_hapus = DataRPM.query.filter(DataRPM.no_lha.in_(lha_target)).all()
    
    if not data_hapus:
        print("⚠️ Data tidak ditemukan. Mungkin sudah terhapus sebelumnya.")
    else:
        jumlah_terhapus = len(data_hapus)
        for item in data_hapus:
            db.session.delete(item)
            
        # Simpan perintah penghapusan ke database
        db.session.commit()
        print(f"✅ SUKSES BERSYUKUR! {jumlah_terhapus} data dummy awal yang error berhasil dihapus permanen.")
