import json
from django.shortcuts import render
from core.api.d2gis import search_places, POPULAR_CITIES

def search_view(request):
    query = request.GET.get("q", "")
    city = request.GET.get("city", "Красноярск")
    category = request.GET.get("category", "")
    
    # Ищем места
    places, city_data = search_places(
        query=query,
        city=city,
        category=category
    )
    
    # Фильтруем кривые точки
    safe_places = []
    for p in places:
        try:
            lat = float(p.get("lat", 0))
            lon = float(p.get("lon", 0))
            if lat != 0 and lon != 0:  # Проверяем, что координаты не нулевые
                safe_places.append(p)
        except:
            continue
    
    # Берем координаты города из city_data
    city_lat = city_data.get("lat")
    city_lon = city_data.get("lon")
    
    # Если нет координат города, используем Красноярск
    if city_lat is None or city_lon is None:
        city_lat = 56.0153
        city_lon = 92.8932
    
    context = {
        "query": query,
        "city": city,
        "category": category,
        "cities": list(POPULAR_CITIES.keys()),
        "places_json": json.dumps(safe_places, ensure_ascii=False),
        "city_lat": city_lat,
        "city_lon": city_lon,
    }
    
    return render(request, "core/search.html", context)

def index(request):
    return search_view(request)