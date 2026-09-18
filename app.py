from flask import Flask, render_template, request, redirect, flash, session, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "kunci_rahasia_untuk_sesi_dan_notifikasi"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db_audit_v5.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# FITUR BARU: Auto-Logout setelah 15 Menit Inaktif
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

# Konfigurasi Upload File
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__name__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg'}

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- SKEMA DATABASE (Sama seperti V5) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    nama_lengkap = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

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
    status_approval = db.Column(db.String(50), nullable=True)
    usulan_status = db.Column(db.String(50), nullable=True)
    usulan_tenggat = db.Column(db.Date, nullable=True)
    no_ba_kesepakatan = db.Column(db.String(100), nullable=True)
    tgl_ba_kesepakatan = db.Column(db.Date, nullable=True)
    file_bukti = db.Column(db.String(200), nullable=True)

# --- FUNGSI GLOBAL NOTIFIKASI KETUA TIM ---
@app.context_processor
def inject_pending_count():
    if session.get('role') == 'ketuatim':
        count = DataRPM.query.filter_by(status_approval='Menunggu Approval').count()
        return dict(pending_count=count)
    return dict(pending_count=0)

# --- FUNGSI KEAMANAN ---
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

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            session.permanent = True # Mengaktifkan timer 15 menit
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

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def admin_dashboard():
    if request.method == 'POST':
        baru = User(
            username=request.form['username'],
            nama_lengkap=request.form['nama_lengkap'],
            password=request.form['password'],
            role=request.form['role']
        )
        db.session.add(baru)
        db.session.commit()
        flash(f"User {baru.nama_lengkap} berhasil ditambahkan!", "success")
        return redirect('/admin')
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/')
@login_required
def dashboard():
    if session.get('role') == 'superadmin': return redirect('/admin')
    hari_ini = date.today()
    data_rpm = DataRPM.query.all()
    for item in data_rpm: item.sisa_hari = (item.tenggat_waktu - hari_ini).days
    data_rpm_sorted = sorted(data_rpm, key=lambda x: (1 if x.status == 'Memadai' else 0, x.sisa_hari))
    return render_template('index.html', data=data_rpm_sorted)

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
    return render_template('form.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('auditor')
def edit_data(id):
    rpm = DataRPM.query.get_or_404(id)
    if request.method == 'POST':
        password_input = request.form['password_otorisasi']
        user = User.query.filter_by(username=session['username'], password=password_input).first()
        if not user:
            flash("Otorisasi Gagal: Password Anda salah!", "danger")
            return redirect(f'/edit/{id}')

        rpm.usulan_status = request.form['status']
        if rpm.usulan_status != rpm.status:
            file = request.files.get('file_bukti')
            if not file or not allowed_file(file.filename):
                flash("WAJIB mengunggah file bukti (PDF/JPG) jika merubah status!", "danger")
                return redirect(f'/edit/{id}')
            filename = secure_filename(f"RPM_{id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            rpm.file_bukti = filename

        rpm.usulan_tenggat = datetime.strptime(request.form['tenggat_waktu'], '%Y-%m-%d').date()
        if rpm.usulan_tenggat != rpm.tenggat_waktu:
            rpm.no_ba_kesepakatan = request.form.get('no_ba')
            rpm.tgl_ba_kesepakatan = datetime.strptime(request.form.get('tgl_ba'), '%Y-%m-%d').date()
            
        rpm.status_approval = 'Menunggu Approval'
        db.session.commit()
        flash("Usulan dan bukti berhasil dikirim ke Ketua Tim Audit!", "success")
        return redirect('/')
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
    password_input = request.form['password_otorisasi']
    user = User.query.filter_by(username=session['username'], password=password_input).first()
    if not user:
        flash("Otorisasi Gagal: Password Anda salah!", "danger")
        return redirect('/approval')

    rpm = DataRPM.query.get_or_404(id)
    action = request.form['action']
    
    if action == 'terima':
        rpm.status = rpm.usulan_status
        if rpm.usulan_tenggat: rpm.tenggat_waktu = rpm.usulan_tenggat
        flash(f"Usulan disetujui! Notifikasi WA telah dikirim.", "success")
    else:
        flash("Usulan perubahan ditolak.", "warning")
        
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
        admin = User(username='admin', nama_lengkap='Administrator', password='admin', role='superadmin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
