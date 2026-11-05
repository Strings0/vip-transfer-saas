from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from models import SessionLocal, Booking, Driver, User, Company, BookingStatus
import uvicorn
from datetime import datetime

# 1. APP NESNESİNİ BURADA TANIMLIYORUZ (Hatanın çözümü)
app = FastAPI(title="VIP Transfer Multi-Tenant SaaS")

# 2. PYDANTIC MODELLERİ
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

# 3. VERİTABANI BAŞLANGIÇ AYARLARI
def init_db():
    session = SessionLocal()
    if session.query(Company).count() == 0:
        c1 = Company(id="C1", name="Doğu VIP Turizm")
        u1 = User(id="U1", company_id="C1", username="dogu_vip", password="123")
        d1 = Driver(id="D1", company_id="C1", full_name="Ahmet Şoför", phone="+90532111", vehicle_plate="34 VIP 01", capacity=4, current_lat=41.0082, current_lon=28.9784)
        session.add_all([c1, u1, d1])
        session.commit()
    session.close()

init_db()

# 4. ENDPOINT'LER (Artık app tanımlı olduğu için hata vermeyecek)
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
    return {"status": "ERROR"}

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

@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    with open("index.html", "r", encoding="utf-8") as f: return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    with open("admin_dashboard.html", "r", encoding="utf-8") as f: return f.read()

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
    # --- ŞOFÖR MOBİL EKRANI API'LERİ ---

class DriverStatusUpdate(BaseModel):
    booking_id: str
    status: str

# 1. Şoförün Görev Detaylarını Çeken API
@app.get("/api/v1/driver/task/{booking_id}")
async def get_driver_task(booking_id: str):
    session = SessionLocal()
    booking = session.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        session.close()
        return {"status": "ERROR", "message": "Görev bulunamadı"}

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

# 2. Şoförün "Transferi Tamamladım" Butonuna Basma API'si
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

# 3. Şoför Mobil Web Sayfasını Sunan Endpoint
@app.get("/driver-task/{booking_id}", response_class=HTMLResponse)
async def serve_driver_page(booking_id: str):
    with open("driver_task.html", "r", encoding="utf-8") as f:
        return f.read()