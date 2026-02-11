import json
from django.shortcuts import render
from core.api.d2gis import search_places
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.api.d2gis import search_places, calculate_distance
from core.api.route_planner import plan_optimal_route

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

@csrf_exempt
def plan_route_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})
    
    try:
        data = json.loads(request.body)
        
        # Получаем данные из запроса
        start_lat = float(data.get('start_lat'))
        start_lon = float(data.get('start_lon'))
        end_type = data.get('end_type', 'start')
        walking_time = int(data.get('walking_time', 60))
        visit_categories = data.get('visit_categories', [])
        radius = float(data.get('radius', 5000))  # в метрах
        
        # Определяем конечную точку
        end_lat = None
        end_lon = None
        end_category = None
        
        if end_type == 'specific':
            end_lat = float(data.get('end_lat'))
            end_lon = float(data.get('end_lon'))
        elif end_type == 'category':
            end_category = data.get('end_category')
        
        # Планируем маршрут
        route_result = plan_optimal_route(
            start_point=(start_lat, start_lon),
            end_type=end_type,
            end_point=(end_lat, end_lon) if end_lat and end_lon else None,
            end_category=end_category,
            walking_time=walking_time,
            visit_categories=visit_categories,
            radius=radius
        )
        
        if route_result['success']:
            return JsonResponse({
                'success': True,
                'route': route_result['route']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': route_result.get('error', 'Ошибка планирования маршрута')
            })
            
    except Exception as e:
        print(f"Ошибка в API маршрутизации: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
def index(request):
    return search_view(request)