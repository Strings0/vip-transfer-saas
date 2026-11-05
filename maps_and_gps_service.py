import requests

def geocode_address(address_text: str):
    """
    OpenStreetMap (Nominatim API) kullanarak metin adresi ÜCRETSİZ 
    ve API keysiz olarak koordinata (Lat, Lon) çevirir.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': f"{address_text}, İstanbul, Turkey",
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'VIPTransferSaaS/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5).json()
        if response and len(response) > 0:
            lat = float(response[0]['lat'])
            lon = float(response[0]['lon'])
            print(f"📍 [MAPPING BAŞARILI]: '{address_text}' -> ({lat}, {lon})")
            return lat, lon
    except Exception as e:
        print(f"⚠️ Mapping Hatası ({e}), Varsayılan Koordinat Alınıyor.")
    
    # Adres bulunamazsa bilinen ana noktaları kontrol et
    addr_lower = address_text.lower()
    if "sabiha" in addr_lower or "saw" in addr_lower:
        return 40.8986, 29.3092  # Sabiha Gökçen
    elif "istanbul airport" in addr_lower or "ist" in addr_lower or "havalimanı" in addr_lower:
        return 41.2753, 28.7519  # İstanbul Havalimanı
    elif "kadıköy" in addr_lower:
        return 40.9801, 29.0270
    
    return 41.0082, 28.9784  # Taksim (Fallback)

def get_real_distance_km(origin_lat, origin_lng, dest_lat, dest_lng):
    """
    OSRM (Open Source Routing Machine) API kullanarak iki nokta arasındaki 
    gerçek karayolu sürüş mesafesini (km) ÜCRETSİZ hesaplar.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}?overview=false"
    try:
        response = requests.get(url, timeout=5).json()
        if response.get("code") == "Ok":
            distance_meters = response["routes"][0]["distance"]
            return round(distance_meters / 1000.0, 2)
    except Exception as e:
        print(f"⚠️ Rotalama Hesaplama Hatası: {e}")
    
    return 10.0