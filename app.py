from flask import Flask, render_template, request, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "kunci_rahasia_untuk_sesi_dan_notifikasi"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db_audit_v4.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- SKEMA DATABASE ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20)) # 'superadmin', 'auditor', 'ketuatim'

class DataRPM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jenis_audit = db.Column(db.String(50))
    unit_kerja = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    tenggat_waktu = db.Column(db.Date)
    nama_pic = db.Column(db.String(100))
    wa_auditee = db.Column(db.String(20))
    nama_auditor = db.Column(db.String(100))
    wa_auditor = db.Column(db.String(20))
    nama_ketua_tim = db.Column(db.String(100))
    wa_ketua_tim = db.Column(db.String(20))
    status = db.Column(db.String(50), default="Dalam Pemantauan")
    
    # Field Approval
    status_approval = db.Column(db.String(50), nullable=True) # 'Menunggu Approval'
    usulan_status = db.Column(db.String(50), nullable=True)
    usulan_tenggat = db.Column(db.Date, nullable=True)
    no_ba_kesepakatan = db.Column(db.String(100), nullable=True)
    tgl_ba_kesepakatan = db.Column(db.Date, nullable=True)

# --- FUNGSI KEAMANAN ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role:
                flash("Anda tidak memiliki akses ke halaman tersebut!", "danger")
                return redirect('/')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- FUNGSI NOTIFIKASI ---
def kirim_notifikasi_wa(status_baru, unit, wa_auditor, wa_pic, wa_ketua):
    pesan = f"Notifikasi RPM: Status tindak lanjut unit {unit} telah disetujui & diupdate menjadi '{status_baru}'."
    print(f"-> WA KE AUDITOR ({wa_auditor}) & KETUA TIM ({wa_ketua}) & PIC ({wa_pic}): {pesan}")

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session['logged_in'] = True
            session['username'] = user.username
            session['role'] = user.role
            
            if user.role == 'superadmin':
                return redirect('/admin')
            return redirect('/')
        else:
            flash("Username atau Password salah!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# 1. Dashboard Super Admin
@app.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def admin_dashboard():
    if request.method == 'POST':
        baru = User(
            username=request.form['username'],
            password=request.form['password'],
            role=request.form['role']
        )
        db.session.add(baru)
        db.session.commit()
        flash("User berhasil ditambahkan!", "success")
        return redirect('/admin')
    
    users = User.query.all()
    return render_template('admin.html', users=users)

# 2. Dashboard Monitoring (Auditor & Ketua Tim)
@app.route('/')
@login_required
def dashboard():
    if session.get('role') == 'superadmin':
        return redirect('/admin')
        
    hari_ini = date.today()
    data_rpm = DataRPM.query.all()
    for item in data_rpm:
        item.sisa_hari = (item.tenggat_waktu - hari_ini).days

    data_rpm_sorted = sorted(data_rpm, key=lambda x: (1 if x.status == 'Memadai' else 0, x.sisa_hari))
    return render_template('index.html', data=data_rpm_sorted)

# 3. Input RPM (Hanya Auditor)
@app.route('/input', methods=['GET', 'POST'])
@login_required
@role_required('auditor')
def input_data():
    if request.method == 'POST':
        tgl_obj = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        baru = DataRPM(
            jenis_audit=request.form['jenis_audit'], unit_kerja=request.form['unit_kerja'], deskripsi=request.form['deskripsi'],
            tenggat_waktu=tgl_obj, nama_pic=request.form['nama_pic'], wa_auditee=request.form['wa_auditee'],
            nama_auditor=request.form['nama_auditor'], wa_auditor=request.form['wa_auditor'],
            nama_ketua_tim=request.form['nama_ketua_tim'], wa_ketua_tim=request.form['wa_ketua_tim']
        )
        db.session.add(baru)
        db.session.commit()
        flash("Data RPM berhasil ditambahkan!", "success")
        return redirect('/')
    return render_template('form.html') # Asumsi form.html sudah ada, cukup tambahkan CSS baru nanti

# 4. Usulkan Perubahan (Hanya Auditor)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('auditor')
def edit_data(id):
    rpm = DataRPM.query.get_or_404(id)
    if request.method == 'POST':
        rpm.usulan_status = request.form['status']
        rpm.usulan_tenggat = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        if rpm.usulan_tenggat != rpm.tenggat_waktu:
            rpm.no_ba_kesepakatan = request.form.get('no_ba')
            rpm.tgl_ba_kesepakatan = datetime.strptime(request.form.get('tgl_ba'), '%Y-%m-%d').date()
            
        rpm.status_approval = 'Menunggu Approval'
        db.session.commit()
        flash("Usulan perubahan berhasil dikirim ke Ketua Tim Audit!", "success")
        return redirect('/')
    return render_template('edit.html', item=rpm)

# 5. Dashboard Approval (Hanya Ketua Tim)
@app.route('/approval', methods=['GET', 'POST'])
@login_required
@role_required('ketuatim')
def approval_dashboard():
    usulan = DataRPM.query.filter_by(status_approval='Menunggu Approval').all()
    return render_template('approval.html', usulan=usulan)

@app.route('/approve/<int:id>/<action>')
@login_required
@role_required('ketuatim')
def process_approval(id, action):
    rpm = DataRPM.query.get_or_404(id)
    if action == 'terima':
        rpm.status = rpm.usulan_status
        if rpm.usulan_tenggat:
            rpm.tenggat_waktu = rpm.usulan_tenggat
        
        # Kirim WA saat di-approve
        kirim_notifikasi_wa(rpm.status, rpm.unit_kerja, rpm.wa_auditor, rpm.wa_auditee, rpm.wa_ketua_tim)
        flash(f"Usulan disetujui! Notifikasi WA telah dikirim.", "success")
    else:
        flash("Usulan perubahan ditolak.", "warning")
        
    rpm.status_approval = None
    rpm.usulan_status = None
    db.session.commit()
    return redirect('/approval')

# --- INISIALISASI DATABASE & AKUN ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin', role='superadmin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
