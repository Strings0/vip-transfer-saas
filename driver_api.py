from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from models import SessionLocal, Driver

app = FastAPI(title="VIP Transfer - Şoför GPS API Servisi")

# Şoförün Telefonundan/Cihazından Gelecek Konum Modeli
class GPSLocationUpdate(BaseModel):
    driver_id: str
    latitude: float
    longitude: float

@app.post("/api/v1/driver/update-location")
async def update_driver_location(gps_data: GPSLocationUpdate):
    session = SessionLocal()
    driver = session.query(Driver).filter(Driver.id == gps_data.driver_id).first()
    
    if not driver:
        session.close()
        raise HTTPException(status_code=404, detail="Şoför bulunamadı.")

    # Şoförün veritabanındaki anlık konumunu güncelle
    driver.current_lat = gps_data.latitude
    driver.current_lon = gps_data.longitude
    session.commit()
    session.close()

    print(f"📡 [GPS ALINDI]: {driver.full_name} -> Konum: ({gps_data.latitude}, {gps_data.longitude})")
    return {"status": "SUCCESS", "message": "Şoför konumu güncellendi."}