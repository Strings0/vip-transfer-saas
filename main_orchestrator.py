import time
from models import SessionLocal, Booking, Driver, Company, BookingStatus
from email_parser import fetch_latest_bookings
from maps_and_gps_service import geocode_address
from advanced_optimizer import find_optimal_driver
from whatsapp_service import send_whatsapp_notification
from datetime import datetime

def setup_demo_data(session):
    if session.query(Company).count() == 0:
        c1 = Company(id="C1", name="Doğu VIP Turizm")
        session.add(c1)
        session.commit()

    if session.query(Driver).count() == 0:
        d1 = Driver(
            id="D1", company_id="C1", full_name="Ahmet Şoför", phone="+905320000001", 
            vehicle_plate="34 VIP 01", capacity=4, current_lat=41.0082, current_lon=28.9784
        )
        d2 = Driver(
            id="D2", company_id="C1", full_name="Ali Şoför", phone="+905320000002", 
            vehicle_plate="34 VIP 02", capacity=8, current_lat=40.9801, current_lon=29.0270
        )
        session.add_all([d1, d2])
        session.commit()

def run_pipeline():
    session = SessionLocal()
    setup_demo_data(session)

    try:
        incoming_bookings = fetch_latest_bookings()
        
        for item in incoming_bookings:
            existing = session.query(Booking).filter(Booking.id == item['booking_id']).first()
            if not existing:
                lat, lon = geocode_address(item['pickup_address'])

                new_booking = Booking(
                    id=item['booking_id'],
                    company_id="C1",
                    customer_name=item['customer_name'],
                    phone_number=item['phone'],
                    passengers=item['passengers'],
                    pickup_address=item['pickup_address'],
                    pickup_lat=lat,
                    pickup_lon=lon,
                    pickup_time=datetime.now(),
                    status=BookingStatus.PENDING
                )
                session.add(new_booking)
                print(f"📩 [YENİ MAİL YAKALANDI]: {item['booking_id']} - {item['customer_name']}")
        session.commit()

        pending_list = session.query(Booking).filter(Booking.company_id == "C1", Booking.status == BookingStatus.PENDING).all()
        active_drivers = session.query(Driver).filter(Driver.company_id == "C1").all()

        for booking in pending_list:
            driver_dicts = [
                {"id": d.id, "name": d.full_name, "capacity": d.capacity, "last_dropoff_location": (d.current_lat, d.current_lon)} 
                for d in active_drivers
            ]

            booking_dict = {
                "id": booking.id,
                "passengers": booking.passengers,
                "pickup_location": (booking.pickup_lat, booking.pickup_lon)
            }

            best_driver = find_optimal_driver(booking_dict, driver_dicts)

            if best_driver:
                booking.assigned_driver_id = best_driver["id"]
                booking.status = BookingStatus.MATCHED
                session.commit()
                send_whatsapp_notification(booking.phone_number, best_driver["name"], "34 VIP 01")
                print(f"✅ [EŞLEŞTİRME SUCCESS]: {booking.id} ({booking.customer_name}) -> {best_driver['name']}")
            else:
                booking.status = BookingStatus.MANUAL
                session.commit()
                print(f"⚠️ [MANUEL ONAY]: {booking.id} için uygun konumda araç bulunamadı.")

    except Exception as e:
        print(f"❌ Otomasyon Hatası: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("\n🚀 [KESİNTİSİZ OTOMASYON MOTORU BAŞLATILDI] (Her 30 saniyede bir kontrol ediliyor...)")
    while True:
        run_pipeline()
        time.sleep(30)  # 30 saniye bekle ve tekrar tara