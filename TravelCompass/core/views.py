import json
from django.shortcuts import render
from core.api.d2gis import search_places

def search_view(request):
    query = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()
    category = request.GET.get("category", "").strip()
    
    places = []
    city_data = None
    error_message = None
    city_found = False
    
    # Обрабатываем только если указан город
    if city:
        places, city_data = search_places(
            query=query,
            city=city,
            category=category
        )
        
        if city_data:
            city_found = True
            if len(places) == 0 and (query or category):
                error_message = f"В городе '{city}' не найдено мест по вашему запросу."
        else:
            error_message = f"Город '{city}' не найден. Проверьте название."
    else:
        # Если город не указан
        error_message = "Введите название города для поиска"
    
    # Определяем координаты для карты
    if city_found and city_data:
        # Используем координаты города из 2GIS
        try:
            # Преобразуем в числа и форматируем с точкой
            city_lat = float(str(city_data["lat"]).replace(',', '.'))
            city_lon = float(str(city_data["lon"]).replace(',', '.'))
            
            # Проверяем диапазон
            if not (-90 <= city_lat <= 90) or not (-180 <= city_lon <= 180):
                raise ValueError("Координаты вне диапазона")
                
        except (ValueError, TypeError) as e:
            print(f"Ошибка координат: {e}, используем Москву")
            city_lat = 55.7558
            city_lon = 37.6176
        
        default_zoom = 12
        has_city = True
        city_name = city_data.get("name", city)
        
        # Для отображения пользователю форматируем с запятой
        city_lat_display = f"{city_lat:.4f}".replace('.', ',')
        city_lon_display = f"{city_lon:.4f}".replace('.', ',')
    else:
        # Город не найден или не введен
        city_lat = 55.7558
        city_lon = 37.6176
        default_zoom = 4
        has_city = False
        city_name = city if city else ""
        city_lat_display = "55,7558"
        city_lon_display = "37,6176"
    
    # Форматируем координаты для JavaScript (с точкой!)
    city_lat_js = f"{city_lat:.6f}"
    city_lon_js = f"{city_lon:.6f}"
    
    context = {
        "query": query,
        "city": city,
        "category": category,
        "places_json": json.dumps(places, ensure_ascii=False),
        "city_lat": city_lat_js,
        "city_lon": city_lon_js, 
        "city_lat_display": city_lat_display,
        "city_lon_display": city_lon_display,
        "default_zoom": default_zoom,
        "has_city": has_city,
        "places_count": len(places),
        "error_message": error_message,
        "city_found": city_found,
        "city_name": city_name,
    }
    
    return render(request, "core/search.html", context)

def index(request):
    return search_view(request)