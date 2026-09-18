from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "kunci_rahasia_untuk_notifikasi"
# Mengubah nama DB menjadi v2 agar Railway membuat tabel baru yang sesuai dengan kolom baru
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db_audit_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Skema Tabel Database (Diperbarui)
class DataRPM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jenis_audit = db.Column(db.String(50))
    unit_kerja = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    tenggat_waktu = db.Column(db.Date)
    wa_auditee = db.Column(db.String(20))
    wa_auditor = db.Column(db.String(20))
    wa_ketua_tim = db.Column(db.String(20))
    status = db.Column(db.String(50), default="Dalam Pemantauan")
    no_ba_kesepakatan = db.Column(db.String(100), nullable=True)
    tgl_ba_kesepakatan = db.Column(db.Date, nullable=True)

# Halaman Dashboard
@app.route('/')
def dashboard():
    hari_ini = date.today()
    data_rpm = DataRPM.query.all()
    
    # Hitung sisa hari untuk setiap baris data
    for item in data_rpm:
        item.sisa_hari = (item.tenggat_waktu - hari_ini).days

    # Logika Prioritas Sorting: 
    # 1. Status 'Memadai' selalu ditaruh paling bawah (Nilai 1 vs 0)
    # 2. Sisa hari diurutkan dari yang terkecil (paling mendekati tenggat)
    data_rpm_sorted = sorted(data_rpm, key=lambda x: (
        1 if x.status == 'Memadai' else 0,
        x.sisa_hari
    ))

    return render_template('index.html', data=data_rpm_sorted)

# Halaman Input Data Baru
@app.route('/input', methods=['GET', 'POST'])
def input_data():
    if request.method == 'POST':
        tgl_obj = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        
        baru = DataRPM(
            jenis_audit=request.form['jenis_audit'],
            unit_kerja=request.form['unit_kerja'],
            deskripsi=request.form['deskripsi'],
            tenggat_waktu=tgl_obj,
            wa_auditee=request.form['wa_auditee'],
            wa_auditor=request.form['wa_auditor'],
            wa_ketua_tim=request.form['wa_ketua_tim']
        )
        db.session.add(baru)
        db.session.commit()
        return redirect('/')
    return render_template('form.html')

# Halaman Ubah (Edit) Data
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_data(id):
    rpm = DataRPM.query.get_or_404(id)
    
    if request.method == 'POST':
        # Otorisasi: Cek apakah input WA Auditor cocok dengan database
        wa_input = request.form['wa_otorisasi']
        if wa_input != rpm.wa_auditor:
            flash("Otorisasi Gagal: Nomor WA Auditor tidak sesuai!", "danger")
            return redirect(f'/edit/{id}')
            
        # Update Status
        rpm.status = request.form['status']
        
        # Cek perubahan tenggat waktu
        new_tgl_obj = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        if new_tgl_obj != rpm.tenggat_waktu:
            no_ba = request.form.get('no_ba')
            tgl_ba = request.form.get('tgl_ba')
            
            if not no_ba or not tgl_ba:
                flash("Nomor dan Tanggal Berita Acara WAJIB diisi jika mengubah tenggat waktu!", "danger")
                return redirect(f'/edit/{id}')
                
            rpm.tenggat_waktu = new_tgl_obj
            rpm.no_ba_kesepakatan = no_ba
            rpm.tgl_ba_kesepakatan = datetime.strptime(tgl_ba, '%Y-%m-%d').date()

        db.session.commit()
        return redirect('/')
        
    return render_template('edit.html', item=rpm)

# Pemicu Pembuatan Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("Menjalankan server...")
    app.run(debug=True)
