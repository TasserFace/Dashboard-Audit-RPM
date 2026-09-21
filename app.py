from flask import Flask, render_template, request, redirect, flash, session, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.exc import IntegrityError
import os
import random
import string
import requests
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "kunci_rahasia_untuk_sesi_dan_notifikasi"

# --- KONFIGURASI API FONNTE ---
FONNTE_TOKEN = "MASUKKAN_TOKEN_API_FONNTE_ANDA_DISINI"

def send_wa_fonnte(target, message):
    url = "https://api.fonnte.com/send"
    headers = {"Authorization": FONNTE_TOKEN}
    data = {"target": target, "message": message}
    try:
        response = requests.post(url, headers=headers, data=data)
        print(f"Status Fonnte: {response.text}")
    except Exception as e:
        print(f"Gagal mengirim pesan WA via Fonnte: {e}")

# --- KONFIGURASI PENYIMPANAN PERMANEN (BRANKAS / VOLUME) ---
# Jika aplikasi berjalan di Railway (mendeteksi folder /app/data), gunakan folder tersebut.
# Jika berjalan di laptop Anda, gunakan folder aplikasi biasa.
if os.path.exists('/app/data'):
    BASE_DIR = '/app/data'
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database dan file upload sekarang disimpan secara dinamis di BASE_DIR
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'db_audit_v8.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- SKEMA DATABASE ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    nama_lengkap = db.Column(db.String(100))
    password = db.Column(db.String(255))
    no_wa = db.Column(db.String(20))
    role = db.Column(db.String(20))

class DataRPM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    no_lha = db.Column(db.String(100)) 
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
    
    status_approval = db.Column(db.String(50), nullable=True)
    usulan_status = db.Column(db.String(50), nullable=True)
    usulan_tenggat = db.Column(db.Date, nullable=True)
    no_ba_kesepakatan = db.Column(db.String(100), nullable=True)
    tgl_ba_kesepakatan = db.Column(db.Date, nullable=True)
    file_bukti = db.Column(db.String(200), nullable=True)
    file_ba_kesepakatan = db.Column(db.String(200), nullable=True)

# --- FUNGSI GLOBAL & KEAMANAN ---
@app.context_processor
def inject_pending_count():
    if session.get('role') == 'ketuatim':
        count = DataRPM.query.filter_by(status_approval='Menunggu Approval').count()
        return dict(pending_count=count)
    return dict(pending_count=0)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session: 
            flash("Sesi Anda telah berakhir. Silakan login kembali.", "warning")
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

# --- ROUTES LOGIN & LOGOUT ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session.permanent = True 
            session['logged_in'] = True
            session['username'] = user.username
            session['nama_lengkap'] = user.nama_lengkap
            session['role'] = user.role
            return redirect('/admin') if user.role == 'superadmin' else redirect('/')
        else:
            flash("Username atau Password salah!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            if not user.no_wa:
                flash("Nomor WA tidak terdaftar untuk akun ini. Hubungi Super Admin.", "danger")
            else:
                new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                user.password = generate_password_hash(new_password)
                db.session.commit()
                pesan_wa = f"Halo *{user.nama_lengkap}*,\n\nBerikut adalah password baru untuk akun SIMA RPM Anda:\n\n🔑 *{new_password}*\n\nSilakan login kembali dan jaga kerahasiaan password ini."
                send_wa_fonnte(user.no_wa, pesan_wa)
                flash(f"Password baru telah berhasil dikirim ke WhatsApp Anda yang terdaftar ({user.no_wa[:4]}xxx).", "success")
                return redirect('/login')
        else:
            flash("Username (PN) tidak ditemukan dalam sistem.", "danger")
    return render_template('forgot_password.html')

# --- ROUTES SUPER ADMIN ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def admin_dashboard():
    if request.method == 'POST':
        try:
            hashed_pw = generate_password_hash(request.form['password'])
            baru = User(
                username=request.form['username'],
                nama_lengkap=request.form['nama_lengkap'],
                password=hashed_pw,
                no_wa=request.form['no_wa'],
                role=request.form['role']
            )
            db.session.add(baru)
            db.session.commit()
            flash(f"User {baru.nama_lengkap} berhasil ditambahkan!", "success")
        except IntegrityError:
            db.session.rollback()
            flash("GAGAL: Username (PN) tersebut sudah terdaftar di sistem!", "danger")
        return redirect('/admin')
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/reset_password/<int:id>', methods=['POST'])
@login_required
@role_required('superadmin')
def admin_reset_password(id):
    user = User.query.get_or_404(id)
    user.password = generate_password_hash(request.form['new_password'])
    db.session.commit()
    flash(f"Password untuk user {user.nama_lengkap} berhasil di-reset!", "success")
    return redirect('/admin')

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
@login_required
@role_required('superadmin')
def admin_delete_user(id):
    user = User.query.get_or_404(id)
    if user.username == session['username']:
        flash("GAGAL: Anda tidak bisa menghapus akun Anda sendiri yang sedang aktif!", "danger")
        return redirect('/admin')
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.nama_lengkap} berhasil dihapus secara permanen.", "success")
    return redirect('/admin')

@app.route('/admin/edit_user/<int:id>', methods=['POST'])
@login_required
@role_required('superadmin')
def admin_edit_user(id):
    user = User.query.get_or_404(id)
    new_role = request.form['role']
    if user.username == session['username'] and new_role != 'superadmin':
        flash("GAGAL: Anda tidak bisa menurunkan hak akses Super Admin Anda sendiri!", "danger")
        return redirect('/admin')
    user.role = new_role
    db.session.commit()
    flash(f"Kewenangan user {user.nama_lengkap} berhasil diubah menjadi {new_role.upper()}.", "success")
    return redirect('/admin')

# --- ROUTE 1: HALAMAN UTAMA (RINGKASAN EKSEKUTIF) ---
@app.route('/')
@login_required
def dashboard_summary():
    if session.get('role') == 'superadmin': return redirect('/admin')
    
    hari_ini = date.today()
    data_rpm = DataRPM.query.all()
    
    total = len(data_rpm)
    selesai = sum(1 for item in data_rpm if item.status == 'Memadai')
    kritis = sum(1 for item in data_rpm if item.status != 'Memadai' and (item.tenggat_waktu - hari_ini).days <= 14)
    proses = sum(1 for item in data_rpm if item.status != 'Memadai' and (item.tenggat_waktu - hari_ini).days > 14)
    
    return render_template('dashboard_summary.html', total=total, selesai=selesai, kritis=kritis, proses=proses)

# --- ROUTE 2: HALAMAN MONITORING (TABEL DAFTAR RPM) ---
@app.route('/monitoring')
@login_required
def monitoring():
    if session.get('role') == 'superadmin': return redirect('/admin')
    
    hari_ini = date.today()
    data_rpm = DataRPM.query.all()
    for item in data_rpm: item.sisa_hari = (item.tenggat_waktu - hari_ini).days
    data_rpm_sorted = sorted(data_rpm, key=lambda x: (1 if x.status == 'Memadai' else 0, x.sisa_hari))
    
    return render_template('index.html', data=data_rpm_sorted)

# --- ROUTES APLIKASI LAINNYA ---
@app.route('/input', methods=['GET', 'POST'])
@login_required
@role_required('auditor')
def input_data():
    if request.method == 'POST':
        tgl_obj = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        baru = DataRPM(
            no_lha=request.form['no_lha'], jenis_audit=request.form['jenis_audit'], unit_kerja=request.form['unit_kerja'], deskripsi=request.form['deskripsi'],
            tenggat_waktu=tgl_obj, nama_pic=request.form['nama_pic'], wa_auditee=request.form['wa_auditee'],
            nama_auditor=request.form['nama_auditor'], wa_auditor=request.form['wa_auditor'],
            nama_ketua_tim=request.form['nama_ketua_tim'], wa_ketua_tim=request.form['wa_ketua_tim']
        )
        db.session.add(baru)
        db.session.commit()
        flash("Data RPM berhasil ditambahkan!", "success")
        return redirect('/monitoring')
    return render_template('form.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('auditor')
def edit_data(id):
    rpm = DataRPM.query.get_or_404(id)
    if request.method == 'POST':
        user = User.query.filter_by(username=session['username']).first()
        if not user or not check_password_hash(user.password, request.form['password_otorisasi']):
            flash("Otorisasi Gagal: Password Akun Anda salah!", "danger")
            return redirect(f'/edit/{id}')

        rpm.usulan_status = request.form['status']
        if rpm.usulan_status != rpm.status:
            file = request.files.get('file_bukti')
            if not file or not allowed_file(file.filename):
                flash("WAJIB mengunggah file bukti status!", "danger")
                return redirect(f'/edit/{id}')
            filename = secure_filename(f"RPM_{id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            rpm.file_bukti = filename

        rpm.usulan_tenggat = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        if rpm.usulan_tenggat != rpm.tenggat_waktu:
            rpm.no_ba_kesepakatan = request.form.get('no_ba')
            rpm.tgl_ba_kesepakatan = datetime.strptime(request.form.get('tgl_ba'), '%Y-%m-%d').date()
            file_ba = request.files.get('file_ba')
            if not file_ba or not allowed_file(file_ba.filename):
                flash("WAJIB mengunggah File BA!", "danger")
                return redirect(f'/edit/{id}')
            filename_ba = secure_filename(f"BA_{id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_ba.filename}")
            file_ba.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_ba))
            rpm.file_ba_kesepakatan = filename_ba
            
        rpm.status_approval = 'Menunggu Approval'
        db.session.commit()
        
        pesan_kt = f"🔔 *Notifikasi SIMA RPM*\n\nTerdapat usulan perubahan status RPM untuk Unit Kerja *{rpm.unit_kerja}* dari Auditor *{rpm.nama_auditor}* yang memerlukan persetujuan Anda.\n\nSilakan cek Menu Approval di Dashboard."
        send_wa_fonnte(rpm.wa_ketua_tim, pesan_kt)
        
        flash("Usulan dikirim ke Ketua Tim Audit dan notifikasi WA telah diteruskan!", "success")
        return redirect('/monitoring')
    return render_template('edit.html', item=rpm)

@app.route('/approval', methods=['GET'])
@login_required
@role_required('ketuatim')
def approval_dashboard():
    usulan = DataRPM.query.filter_by(status_approval='Menunggu Approval').all()
    return render_template('approval.html', usulan=usulan)

@app.route('/process_approval/<int:id>', methods=['POST'])
@login_required
@role_required('ketuatim')
def process_approval(id):
    user = User.query.filter_by(username=session['username']).first()
    if request.form['action'] == 'terima':
        if not user or not check_password_hash(user.password, request.form['password_otorisasi']):
            flash("Otorisasi Gagal: Password Anda salah!", "danger")
            return redirect('/approval')

    rpm = DataRPM.query.get_or_404(id)
    if request.form['action'] == 'terima':
        rpm.status = rpm.usulan_status
        if rpm.usulan_tenggat: rpm.tenggat_waktu = rpm.usulan_tenggat
        
        pesan_approval = f"✅ *Notifikasi SIMA RPM*\n\nUsulan tindak lanjut RPM untuk Unit Kerja *{rpm.unit_kerja}* telah *DISETUJUI* oleh Ketua Tim.\n\nStatus saat ini: *{rpm.status}*"
        send_wa_fonnte(rpm.wa_auditor, pesan_approval) 
        send_wa_fonnte(rpm.wa_auditee, pesan_approval) 
        flash("Usulan disetujui! Notifikasi WA otomatis telah dikirim ke Auditor dan Auditee.", "success")
    else:
        pesan_tolak = f"❌ *Notifikasi SIMA RPM*\n\nUsulan tindak lanjut RPM untuk Unit Kerja *{rpm.unit_kerja}* telah *DITOLAK* oleh Ketua Tim.\nSilakan lakukan revisi."
        send_wa_fonnte(rpm.wa_auditor, pesan_tolak)
        flash("Usulan perubahan ditolak dan notifikasi WA telah dikirim ke Auditor.", "warning")
        
    rpm.status_approval = None
    rpm.usulan_status = None
    db.session.commit()
    return redirect('/approval')

@app.route('/uploads/<name>')
@login_required
def download_file(name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], name)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_hashed = generate_password_hash('admin')
        admin = User(username='admin', nama_lengkap='Administrator', password=admin_hashed, role='superadmin', no_wa='08123456789')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
