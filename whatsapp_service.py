from twilio.rest import Client

# TWILIO CONSOLE'DAN ALINACAK ANAHTARLAR (twilio.com)
TWILIO_ACCOUNT_SID = "AC26ac887f4b182f5f5c107e4105497d66"
TWILIO_AUTH_TOKEN = "e8957334237a3b3a39cc513b313eaeb9"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio Sandbox Numarası

def send_whatsapp_notification(to_phone: str, driver_name: str, plate_number: str):
    # Eğer API Anahtarları girilmişse GERÇEK WhatsApp mesajı atar
    if TWILIO_ACCOUNT_SID != "YOUR_ACCOUNT_SID_HERE":
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message_body = (
                f"Merhaba Sayın Müşterimiz! VIP Transfer rezervasyonunuz onaylanmıştır. 🚗\n\n"
                f"👨‍✈️ Şoförünüz: {driver_name}\n"
                f"🚘 Araç Plakası: {plate_number}\n"
                f"📍 Şoförünüz sizi belirtilen saatte alış noktasında bekliyor olacaktır."
            )
            message = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=message_body,
                to=f"whatsapp:{to_phone}"
            )
            print(f"📱 [GERÇEK WHATSAPP GÖNDERİLDİ] -> SID: {message.sid}")
            return True
        except Exception as e:
            print(f" WhatsApp Mesaj Hatası: {e}")
            return False
    else:
        # API henüz girilmediyse konsola simülasyon basar
        print(f"\n📱 [WHATSAPP SİMÜLASYONU] -> Alıcı: {to_phone}")
        print(f"   Mesaj: Sayın müşterimiz, transfer için şoförünüz {driver_name} ({plate_number}) atanmıştır.\n")
        return True