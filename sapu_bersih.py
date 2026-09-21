from app import app, db, DataRPM

with app.app_context():
    print("Mencari data yang nyangkut dan menyebabkan error di Menu Approval...")
    
    # Sapu bersih SEMUA data yang berstatus Menunggu Approval
    data_nyangkut = DataRPM.query.filter_by(status_approval='Menunggu Approval').all()
    
    if not data_nyangkut:
        print("✅ Tidak ada data approval yang nyangkut. Database bersih.")
    else:
        jumlah = len(data_nyangkut)
        for item in data_nyangkut:
            db.session.delete(item)
            
        db.session.commit()
        print(f"✅ BERHASIL! {jumlah} data approval yang menyebabkan Error 500 telah dihapus permanen.")
