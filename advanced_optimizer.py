import math
from maps_and_gps_service import get_real_distance_km

def find_optimal_driver(booking, drivers, max_radius_km=25.0):
    best_driver = None
    min_distance = float('inf')

    b_lat, b_lon = booking["pickup_location"]

    for driver in drivers:
        # 1. Kısıt: Yolcu Kapasitesi Yeterli mi?
        if driver["capacity"] >= booking["passengers"]:
            d_lat, d_lon = driver["last_dropoff_location"]
            
            # Canlı OSRM Karayolu Mesafesi Hesapla
            distance = get_real_distance_km(b_lat, b_lon, d_lat, d_lon)
            print(f"🔍 Mesafe Kontrolü: {driver['name']} -> Müşteri: {distance} km")

            # 2. Kısıt: Çap ve En Yakın Mesafe Kontrolü
            if distance <= max_radius_km and distance < min_distance:
                min_distance = distance
                best_driver = driver

    return best_driver