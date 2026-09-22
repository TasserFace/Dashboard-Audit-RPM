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

def waktu_sekarang():
    return datetime.utcnow() + timedelta(hours=7)

def hari_ini_wib():
    return waktu_sekarang().date()

FONNTE_TOKEN = "MASUKKAN_TOKEN_API_FONNTE_ANDA_DISINI"

def send_wa_fonnte(target, message):
    url = "https://api.fonnte.com/send"
    headers = {"Authorization": FONNTE_TOKEN}
    data = {"target": target, "message": message}
    try:
        requests.post(url, headers=headers, data=data)
    except Exception as e:
        print(f"Gagal WA Fonnte: {e}")

if os.path.exists('/app/data'):
    BASE_DIR = '/app/data'
else:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'db_audit_v9.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}

db = SQLAlchemy(app)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    
    # KOLOM BARU UNTUK ARGO SLA AUDITOR
    tgl_terima_dokumen = db.Column(db.Date, nullable=True)
    
    status_approval = db.Column(db.String(50), nullable=True)
    usulan_status = db.Column(db.String(50), nullable=True)
    usulan_tenggat = db.Column(db.Date, nullable=True)
    no_ba_kesepakatan = db.Column(db.String(100), nullable=True)
    tgl_ba_kesepakatan = db.Column(db.Date, nullable=True)
    file_bukti = db.Column(db.String(200), nullable=True)
    file_ba_kesepakatan = db.Column(db.String(200), nullable=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    waktu = db.Column(db.DateTime, default=waktu_sekarang)
    username = db.Column(db.String(50))
    nama_lengkap = db.Column(db.String(100))
    role = db.Column(db.String(20))
    aktivitas = db.Column(db.Text)

def bersihkan_log_lama():
    batas_waktu = waktu_sekarang() - timedelta(hours=24)
    ActivityLog.query.filter(ActivityLog.waktu < batas_waktu).delete()

def catat_log(aktivitas):
    if 'username' in session:
        bersihkan_log_lama() 
        log = ActivityLog(username=session['username'], nama_lengkap=session['nama_lengkap'], role=session['role'], aktivitas=aktivitas)
        db.session.add(log)
        db.session.commit()

@app.context_processor
def inject_pending_count():
    if session.get('logged_in') and session.get('role') != 'superadmin':
        count = DataRPM.query.filter_by(status_approval='Menunggu Approval', wa_ketua_tim=session.get('no_wa')).count()
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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'superadmin':
            flash("Anda bukan Super Admin!", "danger")
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

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
            session['no_wa'] = user.no_wa 
            catat_log("Login ke dalam sistem")
            return redirect('/admin') if user.role == 'superadmin' else redirect('/')
        else:
            flash("Username atau Password salah!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    catat_log("Logout dari sistem")
    session.clear()
    return redirect('/login')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            if not user.no_wa:
                flash("Nomor WA tidak terdaftar untuk akun ini.", "danger")
            else:
                new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                user.password = generate_password_hash(new_password)
                db.session.commit()
                send_wa_fonnte(user.no_wa, f"Halo *{user.nama_lengkap}*,\n\nBerikut password baru Anda:\n\n🔑 *{new_password}*")
                flash("Password baru dikirim ke WhatsApp Anda.", "success")
                return redirect('/login')
        else:
            flash("Username tidak ditemukan.", "danger")
    return render_template('forgot_password.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        baru = User(username=request.form['username'], nama_lengkap=request.form['nama_lengkap'], password=hashed_pw, no_wa=request.form['no_wa'], role=request.form['role'])
        db.session.add(baru)
        db.session.commit()
        flash("User berhasil ditambahkan!", "success")
        return redirect('/admin')
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/logs')
@login_required
@admin_required
def admin_logs():
    logs = ActivityLog.query.order_by(ActivityLog.waktu.desc()).limit(500).all()
    return render_template('logs.html', logs=logs)

@app.route('/admin/reset_password/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(id):
    user = User.query.get_or_404(id)
    user.password = generate_password_hash(request.form['new_password'])
    db.session.commit()
    flash(f"Password {user.nama_lengkap} di-reset!", "success")
    return redirect('/admin')

@app.route('/admin/delete_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash("User dihapus.", "success")
    return redirect('/admin')

@app.route('/admin/edit_wa/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_edit_wa(id):
    user = User.query.get_or_404(id)
    user.no_wa = request.form['new_wa']
    db.session.commit()
    flash("Nomor WhatsApp diperbarui!", "success")
    return redirect('/admin')

@app.route('/')
@login_required
def dashboard_summary():
    if session.get('role') == 'superadmin': return redirect('/admin')
    data_rpm = DataRPM.query.all()
    
    # REVISI LOGIKA DASHBOARD (Lebih Jelas Berdasarkan Pemisahan Domain)
    total = len(data_rpm)
    selesai = sum(1 for item in data_rpm if item.status == 'Memadai')
    pemantauan_auditee = sum(1 for item in data_rpm if item.status == 'Dalam Pemantauan' or item.status == 'Belum Memadai')
    reviu_auditor = sum(1 for item in data_rpm if item.status == 'Sedang Direviu Auditor')
    
    return render_template('dashboard_summary.html', total=total, selesai=selesai, pemantauan=pemantauan_auditee, reviu=reviu_auditor)

@app.route('/monitoring')
@login_required
def monitoring():
    if session.get('role') == 'superadmin': return redirect('/admin')
    hari_ini = hari_ini_wib()
    data_rpm = DataRPM.query.all()
    
    # LOGIKA ARGO SLA GANDA (Auditee vs Auditor)
    for item in data_rpm:
        if item.status == 'Dalam Pemantauan' or item.status == 'Belum Memadai':
            item.sisa_hari = (item.tenggat_waktu - hari_ini).days
        elif item.status == 'Sedang Direviu Auditor' and item.tgl_terima_dokumen:
            batas_reviu = item.tgl_terima_dokumen + timedelta(days=10)
            item.sisa_hari = (batas_reviu - hari_ini).days
        else:
            item.sisa_hari = 0
            
    # Urutkan: Yang kritis/telat di atas
    data_rpm_sorted = sorted(data_rpm, key=lambda x: (1 if x.status == 'Memadai' else 0, x.sisa_hari))
    return render_template('index.html', data=data_rpm_sorted)

@app.route('/input', methods=['GET', 'POST'])
@login_required
def input_data():
    if session.get('role') == 'superadmin': return redirect('/admin')
    if request.method == 'POST':
        wa_ketua_input = request.form['wa_ketua_tim'].strip()
        if wa_ketua_input == session.get('no_wa'):
            flash("PENOLAKAN SISTEM: Anda tidak dapat menunjuk diri sendiri sebagai Ketua Tim!", "danger")
            return redirect('/input')

        tgl_obj = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        baru = DataRPM(
            no_lha=request.form['no_lha'], jenis_audit=request.form['jenis_audit'], unit_kerja=request.form['unit_kerja'], deskripsi=request.form['deskripsi'],
            tenggat_waktu=tgl_obj, nama_pic=request.form['nama_pic'], wa_auditee=request.form['wa_auditee'],
            nama_auditor=request.form['nama_auditor'], wa_auditor=request.form['wa_auditor'],
            nama_ketua_tim=request.form['nama_ketua_tim'], wa_ketua_tim=wa_ketua_input
        )
        db.session.add(baru)
        db.session.commit()
        catat_log(f"Menambahkan RPM (LHA: {baru.no_lha})")
        flash("Data RPM ditambahkan!", "success")
        return redirect('/monitoring')
    return render_template('form.html')

# RUTE BARU: TERIMA DOKUMEN & MULAI ARGO 10 HARI AUDITOR
@app.route('/terima_dokumen/<int:id>', methods=['POST'])
@login_required
def terima_dokumen(id):
    rpm = DataRPM.query.get_or_404(id)
    if rpm.wa_auditor != session.get('no_wa'):
        flash("AKSES DITOLAK: Anda bukan Auditor PIC di LHA ini!", "danger")
        return redirect('/monitoring')
        
    rpm.status = "Sedang Direviu Auditor"
    rpm.tgl_terima_dokumen = hari_ini_wib()
    db.session.commit()
    
    catat_log(f"Menerima dokumen TL (LHA: {rpm.no_lha}). Argo SLA 10 Hari Auditor Dimulai.")
    flash("Dokumen telah diterima! Argo batas waktu reviu Auditor 10 hari telah berjalan.", "success")
    return redirect('/monitoring')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_data(id):
    if session.get('role') == 'superadmin': return redirect('/admin')
    rpm = DataRPM.query.get_or_404(id)
    if rpm.wa_auditor != session.get('no_wa'):
        flash("AKSES DITOLAK: Anda bukan Auditor PIC!", "danger")
        return redirect('/monitoring')
        
    if request.method == 'POST':
        user = User.query.filter_by(username=session['username']).first()
        if not user or not check_password_hash(user.password, request.form['password_otorisasi']):
            flash("Otorisasi Gagal: Password salah!", "danger")
            return redirect(f'/edit/{id}')

        rpm.usulan_status = request.form['status']
        if rpm.usulan_status != rpm.status:
            file = request.files.get('file_bukti')
            if not file or not allowed_file(file.filename):
                flash("WAJIB mengunggah file bukti status!", "danger")
                return redirect(f'/edit/{id}')
            filename = secure_filename(f"RPM_{id}_{waktu_sekarang().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            rpm.file_bukti = filename

        rpm.usulan_tenggat = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        if rpm.usulan_tenggat != rpm.tenggat_waktu:
            rpm.no_ba_kesepakatan = request.form.get('no_ba')
            rpm.tgl_ba_kesepakatan = datetime.strptime(request.form.get('tgl_ba'), '%Y-%m-%d').date()
            file_ba = request.files.get('file_ba')
            if file_ba and allowed_file(file_ba.filename):
                filename_ba = secure_filename(f"BA_{id}_{waktu_sekarang().strftime('%Y%m%d%H%M%S')}_{file_ba.filename}")
                file_ba.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_ba))
                rpm.file_ba_kesepakatan = filename_ba
            
        rpm.status_approval = 'Menunggu Approval'
        db.session.commit()
        send_wa_fonnte(rpm.wa_ketua_tim, f"🔔 Usulan keputusan RPM LHA {rpm.no_lha} siap untuk Anda reviu di Menu Approval.")
        flash("Usulan keputusan dikirim ke Ketua Tim!", "success")
        return redirect('/monitoring')
    return render_template('edit.html', item=rpm)

@app.route('/request_delete/<int:id>', methods=['POST'])
@login_required
def request_delete(id):
    rpm = DataRPM.query.get_or_404(id)
    if rpm.wa_auditor != session.get('no_wa'):
        flash("AKSES DITOLAK!", "danger")
        return redirect('/monitoring')
        
    user = User.query.filter_by(username=session['username']).first()
    if not user or not check_password_hash(user.password, request.form['password_otorisasi']):
        flash("Otorisasi Gagal: Password salah!", "danger")
        return redirect('/monitoring')

    rpm.usulan_status = 'HAPUS'
    rpm.status_approval = 'Menunggu Approval'
    db.session.commit()
    send_wa_fonnte(rpm.wa_ketua_tim, f"⚠️ Usulan PENGHAPUSAN RPM LHA {rpm.no_lha}.")
    flash("Usulan penghapusan dikirim ke Ketua Tim.", "warning")
    return redirect('/monitoring')

@app.route('/approval', methods=['GET'])
@login_required
def approval_dashboard():
    if session.get('role') == 'superadmin': return redirect('/admin')
    usulan = DataRPM.query.filter_by(status_approval='Menunggu Approval', wa_ketua_tim=session.get('no_wa')).all()
    return render_template('approval.html', usulan=usulan)

@app.route('/process_approval/<int:id>', methods=['POST'])
@login_required
def process_approval(id):
    rpm = DataRPM.query.get_or_404(id)
    if rpm.wa_ketua_tim != session.get('no_wa'):
        flash("AKSES DITOLAK!", "danger")
        return redirect('/approval')
        
    user = User.query.filter_by(username=session['username']).first()
    action = request.form['action']
    if action == 'terima' and (not user or not check_password_hash(user.password, request.form['password_otorisasi'])):
        flash("Otorisasi Gagal!", "danger")
        return redirect('/approval')

    if rpm.usulan_status == 'HAPUS':
        if action == 'terima':
            no_lha = rpm.no_lha
            db.session.delete(rpm)
            db.session.commit()
            send_wa_fonnte(rpm.wa_auditor, f"✅ Usulan penghapusan LHA {no_lha} disetujui.")
            flash("RPM dihapus permanen.", "success")
        else:
            rpm.status_approval = None
            rpm.usulan_status = None
            db.session.commit()
            flash("Usulan penghapusan ditolak.", "warning")
    else:
        if action == 'terima':
            rpm.status = rpm.usulan_status
            if rpm.usulan_tenggat: rpm.tenggat_waktu = rpm.usulan_tenggat
            send_wa_fonnte(rpm.wa_auditor, f"✅ Usulan status LHA {rpm.no_lha} disetujui (Menjadi {rpm.status}).")
            rpm.status_approval = None
            rpm.usulan_status = None
            db.session.commit()
            flash("Usulan disetujui!", "success")
        else:
            rpm.status_approval = None
            rpm.usulan_status = None
            db.session.commit()
            flash("Usulan ditolak. Status dikembalikan ke kondisi sebelumnya.", "warning")
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
