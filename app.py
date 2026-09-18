from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
# Gunakan SQLite untuk kemudahan pengujian tanpa instalasi tambahan
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db_audit_local.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Skema Tabel Database (Lemari Arsip)
class DataRPM(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_kerja = db.Column(db.String(100))
    deskripsi = db.Column(db.Text)
    tenggat_waktu = db.Column(db.Date)
    wa_auditor = db.Column(db.String(20))
    wa_auditee = db.Column(db.String(20))
    status = db.Column(db.String(50), default="Dalam Pemantauan")

# Halaman Dashboard (Papan Rekapitulasi)
@app.route('/')
def dashboard():
    data_rpm = DataRPM.query.all()
    return render_template('index.html', data=data_rpm)

# Halaman Input Data (Formulir Bukti)
@app.route('/input', methods=['GET', 'POST'])
def input_data():
    if request.method == 'POST':
        tgl_str = request.form['tenggat_waktu']
        tgl_obj = datetime.strptime(tgl_str, '%Y-%m-%d').date()
        
        baru = DataRPM(
            unit_kerja=request.form['unit_kerja'],
            deskripsi=request.form['deskripsi'],
            tenggat_waktu=tgl_obj,
            wa_auditor=request.form['wa_auditor'],
            wa_auditee=request.form['wa_auditee']
        )
        db.session.add(baru)
        db.session.commit()
        return redirect('/')
    return render_template('form.html')

# Endpoint untuk mengubah status menjadi 'Memadai'
@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    rpm = DataRPM.query.get_or_404(id)
    rpm.status = "Memadai"
    db.session.commit()
    return redirect('/')

# Memicu pembuatan database sebelum request pertama masuk
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("Menjalankan server...")
    app.run(debug=True)
