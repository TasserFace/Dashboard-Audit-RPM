from app import app, db, User

with app.app_context():
    print("Mencari user dengan role lama...")
    
    # Mencari semua user yang bukan superadmin
    users = User.query.filter(User.role != 'superadmin').all()
    
    jumlah = 0
    for u in users:
        if u.role != 'auditor':
            u.role = 'auditor'
            jumlah += 1
            
    db.session.commit()
    print(f"✅ SUKSES! Berhasil mengubah {jumlah} data user menjadi role 'auditor'.")
