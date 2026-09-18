import os, requests
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import DataRPM # Import skema dari app.py
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DB_URL'))
Session = sessionmaker(bind=engine)
session = Session()

def kirim_wa(nomor_tujuan, pesan):
    # Contoh menggunakan API Fonnte
    url = "https://api.fonnte.com/send"
    headers = {'Authorization': os.getenv('WA_TOKEN')}
    data = {'target': nomor_tujuan, 'message': pesan}
    requests.post(url, headers=headers, data=data)
    print(f"Pesan terkirim ke {nomor_tujuan}")

def evaluasi_harian():
    print("Mulai pengecekan harian...")
    hari_ini = date.today()
    
    # Cari semua data yang statusnya BUKAN 'Memadai'
    rpm_aktif = session.query(DataRPM).filter(DataRPM.status != 'Memadai').all()
    
    for rpm in rpm_aktif:
        sisa_hari = (rpm.tenggat_waktu - hari_ini).days
        
        # LOGIKA 4: Overdue
        if sisa_hari < 0:
            rpm.status = "Overdue"
            session.commit()
            pesan = f"[ESKALASI] Peringatan! Rencana perbaikan {rpm.unit_kerja} telah MELEWATI TENGGAT WAKTU. Harap segera ditindaklanjuti."
            kirim_wa(f"{rpm.wa_auditee},{rpm.wa_auditor}", pesan) # Kirim ke keduanya
            
        # LOGIKA 1 & 2: Pengingat H-14 dan H-7 (Hanya Auditee)
        elif sisa_hari in [14, 7]:
            pesan = f"Pengingat: Rencana perbaikan unit {rpm.unit_kerja} memiliki sisa waktu {sisa_hari} hari. Silakan siapkan bukti perbaikan."
            kirim_wa(rpm.wa_auditee, pesan)
            
        # LOGIKA 1 & 2: Kritis H-3 dan H-1 (Auditee & Auditor)
        elif sisa_hari in [3, 1]:
            pesan = f"[KRITIS] Rencana perbaikan {rpm.unit_kerja} sisa {sisa_hari} hari lagi! Batas akhir: {rpm.tenggat_waktu}."
            kirim_wa(f"{rpm.wa_auditee},{rpm.wa_auditor}", pesan)

if __name__ == "__main__":
    evaluasi_harian()
