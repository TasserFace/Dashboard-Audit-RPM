from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "kunci_rahasia_untuk_sesi_dan_notifikasi"
# Mengubah nama DB ke v3 untuk skema baru (Nama PIC, Nama Auditor, dll)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db_audit_v3.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Skema Tabel Database (Diperbarui dengan Nama-Nama)
class DataRPM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jenis_audit = db.Column(db.String(50))
    unit_kerja = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    tenggat_waktu = db.Column(db.Date)
    
    nama_pic = db.Column(db.String(100))
    wa_auditee = db.Column(db.String(20)) # Nomor WA PIC
    
    nama_auditor = db.Column(db.String(100))
    wa_auditor = db.Column(db.String(20))
    
    nama_ketua_tim = db.Column(db.String(100))
    wa_ketua_tim = db.Column(db.String(20))
    
    status = db.Column(db.String(50), default="Dalam Pemantauan")
    no_ba_kesepakatan = db.Column(db.String(100), nullable=True)
    tgl_ba_kesepakatan = db.Column(db.Date, nullable=True)

# Fungsi Pengecekan Login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Simulasi Pengiriman Notifikasi WA
def kirim_notifikasi_wa(status_baru, unit, wa_auditor, wa_pic, wa_ketua):
    pesan = f"Notifikasi RPM: Status tindak lanjut untuk unit {unit} telah diupdate menjadi '{status_baru}'."
    # Di sini nantinya kita sisipkan kode API Fonnte/Wablas. 
    # Untuk sekarang, sistem mencetak log di terminal server.
    print(f"-> MENGIRIM WA KE AUDITOR ({wa_auditor}): {pesan}")
    print(f"-> MENGIRIM WA KE PIC ({wa_pic}): {pesan}")
    print(f"-> MENGIRIM WA KE KETUA TIM ({wa_ketua}): {pesan}")

# ================= ROUTES ================= #

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Kredensial sementara: admin / admin
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            return redirect('/')
        else:
            flash("Username atau Password salah!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect('/login')

@app.route('/')
@login_required
def dashboard():
    hari_ini = date.today()
    data_rpm = DataRPM.query.all()
    
    for item in data_rpm:
        item.sisa_hari = (item.tenggat_waktu - hari_ini).days

    data_rpm_sorted = sorted(data_rpm, key=lambda x: (
        1 if x.status == 'Memadai' else 0,
        x.sisa_hari
    ))
    return render_template('index.html', data=data_rpm_sorted)

@app.route('/input', methods=['GET', 'POST'])
@login_required
def input_data():
    if request.method == 'POST':
        tgl_obj = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        baru = DataRPM(
            jenis_audit=request.form['jenis_audit'],
            unit_kerja=request.form['unit_kerja'],
            deskripsi=request.form['deskripsi'],
            tenggat_waktu=tgl_obj,
            nama_pic=request.form['nama_pic'],
            wa_auditee=request.form['wa_auditee'],
            nama_auditor=request.form['nama_auditor'],
            wa_auditor=request.form['wa_auditor'],
            nama_ketua_tim=request.form['nama_ketua_tim'],
            wa_ketua_tim=request.form['wa_ketua_tim']
        )
        db.session.add(baru)
        db.session.commit()
        flash("Data RPM berhasil ditambahkan!", "success")
        return redirect('/')
    return render_template('form.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_data(id):
    rpm = DataRPM.query.get_or_404(id)
    if request.method == 'POST':
        # Otorisasi menggunakan password Akun (admin)
        password_input = request.form['password_otorisasi']
        if password_input != 'admin':
            flash("Otorisasi Gagal: Password akun salah!", "danger")
            return redirect(f'/edit/{id}')
            
        status_lama = rpm.status
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
        
        # Kirim notifikasi WA jika status berubah
        if status_lama != rpm.status:
            kirim_notifikasi_wa(rpm.status, rpm.unit_kerja, rpm.wa_auditor, rpm.wa_auditee, rpm.wa_ketua_tim)
            flash(f"Status berhasil diubah menjadi '{rpm.status}'. Notifikasi telah dikirim ke Auditor, PIC, dan Ketua Tim.", "success")

        return redirect('/')
    return render_template('edit.html', item=rpm)

# Inisialisasi Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
