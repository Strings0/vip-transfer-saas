import imaplib
import email
import re
from datetime import datetime

IMAP_SERVER = "imap.gmail.com"
# BURAYA TRANSFER ŞİRKETİNİN GMAIL ADRESİ VE UYGULAMA ŞİFRESİ GELECEK
EMAIL_ACCOUNT = "lifeisgoodbussines@gmail.com" 
EMAIL_PASSWORD = "yyux nyas ejje slco"  # Google Uygulama Şifresi (App Password)

def connect_to_email():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    return mail

def parse_booking_email_body(email_body):
    booking_data = {}
    
    # 1. Rezervasyon No (BK-123456)
    ref_match = re.search(r'(?:Ref|Rezervasyon No|Booking ID):\s*([A-Z0-9\-]+)', email_body, re.IGNORECASE)
    booking_data['booking_id'] = ref_match.group(1) if ref_match else f"BK-{int(datetime.now().timestamp())}"

    # 2. Müşteri Adı
    name_match = re.search(r'(?:Müşteri|Passenger|Guest|Ad Soyad):\s*([A-Za-z\s]+)', email_body)
    booking_data['customer_name'] = name_match.group(1).strip() if name_match else "Misafir Müşteri"

    # 3. Telefon Numarası
    phone_match = re.search(r'\+?\d{10,14}', email_body)
    booking_data['phone'] = phone_match.group(0) if phone_match else "+905000000000"

    # 4. Kişi Sayısı (PAX)
    pax_match = re.search(r'(\d+)\s*(?:pax|kişi|passenger)', email_body, re.IGNORECASE)
    booking_data['passengers'] = int(pax_match.group(1)) if pax_match else 1

    # 5. Alış ve Bırakış Adresleri
    pickup_match = re.search(r'(?:Alış|Pickup):\s*(.+)', email_body)
    booking_data['pickup_address'] = pickup_match.group(1).strip() if pickup_match else "İstanbul Airport"

    # 6. Tarih ve Saat Parse
    time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', email_body)
    booking_data['pickup_time'] = time_match.group(1) if time_match else datetime.now().strftime("%Y-%m-%d %H:%M")

    return booking_data

def fetch_latest_bookings():
    try:
        mail = connect_to_email()
        mail.select("inbox")
        status, messages = mail.search(None, '(UNSEEN SUBJECT "Booking")')
        email_ids = messages[0].split()
        parsed_bookings = []
        
        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore') if not msg.is_multipart() else ""
                    parsed_bookings.append(parse_booking_email_body(body))
        mail.logout()
        return parsed_bookings
    except Exception as e:
        print(f" Canlı E-posta Alınamadı ({e}), Test Verisi İle Devam Ediliyor...")
        return [{
            'booking_id': 'BK-998231',
            'customer_name': 'Sarah Connor',
            'phone': '+905321112233',
            'passengers': 4,
            'pickup_address': 'Sabiha Gökçen Havalimanı',
            'pickup_time': '2026-11-06 14:30'
        }]