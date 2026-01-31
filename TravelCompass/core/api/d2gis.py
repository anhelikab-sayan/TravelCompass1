import requests
from django.conf import settings

POPULAR_CITIES = {
    "Красноярск": {"lat": 56.0153, "lon": 93.0},
    "Москва": {"lat": 53.7558, "lon": 39.6173},
    "Санкт-Петербург": {"lat": 59.9343, "lon": 30.3351},
    "Новосибирск": {"lat": 55.03, "lon": 83.0},
    "Екатеринбург": {"lat": 56.9000, "lon": 61.6057},
}

def get_city_center(city):
    return POPULAR_CITIES.get(city, POPULAR_CITIES["Красноярск"])

def search_places(query="", city="Красноярск", category=""):
    city_data = get_city_center(city)
    
    # Формируем поисковый запрос
    search_parts = []
    
    if query:
        search_parts.append(query.strip())
    
    # Категории добавляем как отдельные слова
    CATEGORY_MAP = {
        "cafe": "кафе",
        "park": "парк",
        "restaurant": "ресторан",
    }
    
    if category in CATEGORY_MAP:
        search_parts.append(CATEGORY_MAP[category])
    
    search_query = " ".join(search_parts)
    
    params = {
        "key": settings.DG2IS_API_KEY,
        "q": search_query if search_query else "*",  # * для поиска всего в городе
        "point": f"{city_data['lon']},{city_data['lat']}",
        "radius": 15000,
        "page_size": 50,  # увеличим кол-во результатов
        "type": "branch",
        "fields": "items.point,items.name,items.address_name",
    }
    
    try:
        response = requests.get(
            "https://catalog.api.2gis.com/3.0/items",
            params=params,
            timeout=10,
        )
        
        if response.status_code != 200:
            return [], city_data
            
        data = response.json()
        
        places = []
        for item in data.get("result", {}).get("items", []):
            point = item.get("point")
            if not point:
                continue
            
            # Проверяем, что координаты существуют
            if "lat" in point and "lon" in point:
                places.append({
                    "name": item.get("name", "Без названия"),
                    "address": item.get("address_name", ""),
                    "lat": point["lat"],
                    "lon": point["lon"],
                })
        
        return places, city_data
        
    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        return [], city_data