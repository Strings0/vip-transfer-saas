from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from models import SessionLocal, Booking, Driver, User, Company, BookingStatus
import uvicorn
from datetime import datetime
import asyncio
import time

# Eğer main_orchestrator veya email_parser içindeki mail kontrol fonksiyonunun adı farklıysa burayı düzenleyebilirsin
try:
    import main_orchestrator
except ImportError:
    main_orchestrator = None

app = FastAPI(title="VIP Transfer Multi-Tenant SaaS")

# ARKA PLAN MAIL DİNLENME GÖREVİ (FREE TIER UYUMLU)
def check_emails_loop():
    while True:
        try:
            if main_orchestrator and hasattr(main_orchestrator, 'run_once'):
                main_orchestrator.run_once()
            elif main_orchestrator and hasattr(main_orchestrator, 'main'):
                main_orchestrator.main()
            print("📧 [MAIL CHECKER]: Mailler kontrol edildi...")
        except Exception as e:
            print(f"⚠️ [MAIL CHECKER HATA]: {e}")
        time.sleep(30) # 30 saniyede bir mailleri tarar

@app.on_event("startup")
async def start_mail_listener():
    if main_orchestrator:
        asyncio.create_task(asyncio.to_thread(check_emails_loop))
        print("🚀 [SYSTEM]: Mail dinleyici arka planda başlatıldı!")

# PYDANTIC MODELLERİ
class LoginRequest(BaseModel):
    username: str
    password: str

class DriverAddRequest(BaseModel):
    company_id: str
    full_name: str
    phone: str
    vehicle_plate: str
    capacity: int

class ManualAssignRequest(BaseModel):
    booking_id: str
    driver_id: str

class DriverStatusUpdate(BaseModel):
    booking_id: str
    status: str

# VERİTABANI BAŞLANGIÇ TOHUMU
def init_db():
    session = SessionLocal()
    company = session.query(Company).filter(Company.id == "C1").first()
    if not company:
        company = Company(id="C1", name="Doğu VIP Turizm")
        session.add(company)
        session.commit()

    user = session.query(User).filter(User.username == "dogu_vip").first()
    if not user:
        u1 = User(id="U1", company_id="C1", username="dogu_vip", password="123")
        session.add(u1)
        session.commit()

    driver = session.query(Driver).filter(Driver.id == "D1").first()
    if not driver:
        d1 = Driver(id="D1", company_id="C1", full_name="Ahmet Şoför", phone="+90532111", vehicle_plate="34 VIP 01", capacity=4, current_lat=41.0082, current_lon=28.9784)
        session.add(d1)
        session.commit()

    session.close()

init_db()

# API ENDPOINT'LERİ

@app.post("/api/v1/login")
async def login(req: LoginRequest):
    session = SessionLocal()
    user = session.query(User).filter(User.username == req.username, User.password == req.password).first()
    session.close()
    if user:
        return {"status": "SUCCESS", "company_id": user.company_id}
    return JSONResponse(status_code=400, content={"status": "ERROR", "message": "Kullanıcı adı veya şifre hatalı"})

@app.post("/api/v1/driver/add")
async def add_driver(req: DriverAddRequest):
    session = SessionLocal()
    new_driver = Driver(
        id=f"D-{int(datetime.now().timestamp())}",
        company_id=req.company_id,
        full_name=req.full_name,
        phone=req.phone,
        vehicle_plate=req.vehicle_plate,
        capacity=req.capacity,
        current_lat=41.0082, current_lon=28.9784
    )
    session.add(new_driver)
    session.commit()
    session.close()
    return {"status": "SUCCESS"}

@app.post("/api/v1/booking/manual-assign")
async def manual_assign(req: ManualAssignRequest):
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == req.booking_id).first()
    
    if booking and req.driver_id:
        booking.assigned_driver_id = req.driver_id
        booking.status = BookingStatus.MATCHED
        session.commit()
        session.refresh(booking)
        session.close()
        print(f"👉 [MANUEL ATAMA BAŞARILI]: {req.booking_id} -> {req.driver_id}")
        return {"status": "SUCCESS"}
    
    session.close()
    return JSONResponse(status_code=400, content={"status": "ERROR"})

@app.get("/api/v1/dashboard-data")
async def get_dashboard_data(company_id: str = "C1"):
    session = SessionLocal()
    bookings = session.query(Booking).filter(Booking.company_id == company_id).all()
    drivers = session.query(Driver).filter(Driver.company_id == company_id).all()
    
    booking_list = []
    for b in bookings:
        status_str = b.status.value if hasattr(b.status, 'value') else str(b.status)
        
        driver_name = "Atanmadı"
        if b.assigned_driver_id:
            d = session.query(Driver).filter(Driver.id == b.assigned_driver_id).first()
            if d:
                driver_name = d.full_name

        booking_list.append({
            "id": b.id,
            "customer_name": b.customer_name,
            "pickup_address": b.pickup_address,
            "pickup_lat": b.pickup_lat,
            "pickup_lon": b.pickup_lon,
            "driver_name": driver_name,
            "status": status_str
        })

    driver_list = [{"id": d.id, "name": d.full_name, "plate": d.vehicle_plate} for d in drivers]
    session.close()

    return {"bookings": booking_list, "drivers": driver_list}

@app.get("/api/v1/driver/task/{booking_id}")
async def get_driver_task(booking_id: str):
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        booking = Booking(
            id=booking_id,
            company_id="C1",
            customer_name="Doğu Bey Canlı Test",
            phone_number="+905329998877",
            passengers=3,
            pickup_address="Taksim Meydanı",
            pickup_lat=41.0082,
            pickup_lon=28.9784,
            pickup_time=datetime.now(),
            status=BookingStatus.MATCHED
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)

    status_str = booking.status.value if hasattr(booking.status, 'value') else str(booking.status)

    data = {
        "booking_id": booking.id,
        "customer_name": booking.customer_name,
        "phone": booking.phone_number,
        "passengers": booking.passengers,
        "pickup_address": booking.pickup_address,
        "status": status_str
    }
    session.close()
    return {"status": "SUCCESS", "task": data}

@app.post("/api/v1/driver/update-task")
async def update_driver_task(req: DriverStatusUpdate):
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == req.booking_id).first()
    
    if booking:
        if req.status == "COMPLETED":
            booking.status = BookingStatus.COMPLETED
        session.commit()
        session.close()
        print(f"🏁 [TRANSFER TAMAMLANTI]: {req.booking_id}")
        return {"status": "SUCCESS"}
    
    session.close()
    return {"status": "ERROR"}

# SAYFA ROUTE'LARI
@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    with open("admin_dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/driver-task/{booking_id}", response_class=HTMLResponse)
async def serve_driver_page(booking_id: str):
    with open("driver_task.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
@app.get("/api/v1/check-now")
async def check_now():
    if main_orchestrator:
        try:
            # main_orchestrator içindeki çalıştırma fonksiyonunu tetikler
            if hasattr(main_orchestrator, 'run_once'):
                main_orchestrator.run_once()
            elif hasattr(main_orchestrator, 'main'):
                main_orchestrator.main()
            return {"status": "SUCCESS", "message": "Mail taraması tetiklendi."}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    return {"status": "ERROR", "message": "main_orchestrator import edilemedi!"}