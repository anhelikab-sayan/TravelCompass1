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
import logging
logger = logging.getLogger(__name__)
# views.py - исправляем функцию plan_route_api
# views.py - добавляем больше логирования в plan_route_api
@csrf_exempt
def plan_route_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})
    
    try:
        data = json.loads(request.body)
        
        logger.info("=" * 60)
        logger.info("ПОЛУЧЕН ЗАПРОС НА МАРШРУТ:")
        logger.info(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("=" * 60)
        
        # Получаем данные из запроса
        start_lat = float(data.get('start_lat'))
        start_lon = float(data.get('start_lon'))
        end_type = data.get('end_type', 'start')
        walking_time = int(data.get('walking_time', 60))
        visit_categories = data.get('visit_categories', [])
        radius = float(data.get('radius', 5000))
        city_name = data.get('city_name', '')
        
        logger.info(f"ОБРАБОТАННЫЕ ДАННЫЕ:")
        logger.info(f"  Начало: {start_lat}, {start_lon}")
        logger.info(f"  Тип конца: {end_type}")
        logger.info(f"  Время: {walking_time} мин")
        logger.info(f"  Категории: {visit_categories}")
        logger.info(f"  Радиус: {radius} м")
        logger.info(f"  Город: {city_name}")
        
        if not start_lat or not start_lon:
            return JsonResponse({'success': False, 'error': 'Не указана начальная точка'})
        
        if not visit_categories:
            logger.warning("НЕТ ВЫБРАННЫХ КАТЕГОРИЙ!")
            return JsonResponse({'success': False, 'error': 'Не выбраны категории для посещения'})
        
        start_point = (float(start_lat), float(start_lon))
        
        # Дополнительные параметры
        end_lat = data.get('end_lat')
        end_lon = data.get('end_lon')
        end_point = (float(end_lat), float(end_lon)) if end_lat and end_lon else None
        end_category = data.get('end_category')
        
        # ВАЖНО: Используем город из запроса, если он есть
        if not city_name and 'city' in data:
            city_name = data.get('city')
        
        logger.info(f"ГОРОД ДЛЯ ПОИСКА (финальный): '{city_name}'")
        
        # Вызываем функцию планирования маршрута
        result = plan_optimal_route(
            start_point=start_point,
            end_type=end_type,
            end_point=end_point,
            end_category=end_category,
            walking_time=walking_time,
            visit_categories=visit_categories,
            radius=radius,
            city_name=city_name
        )
        
        logger.info(f"РЕЗУЛЬТАТ МАРШРУТА: success={result.get('success')}")
        if result.get('success') and result.get('route'):
            points_count = len(result['route'].get('intermediate_points', []))
            logger.info(f"  Промежуточных точек: {points_count}")
            if points_count > 0:
                for i, point in enumerate(result['route']['intermediate_points'][:3]):
                    logger.info(f"    Точка {i+1}: {point['name']} - {point['distance']:.0f}м")
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Ошибка в API маршрута: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})