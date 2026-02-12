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
        
        # Получаем адреса, если есть
        start_address = data.get('start_address', 'Начальная точка')
        
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
        end_address = data.get('end_address', '')
        
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
        
        # Сохраняем маршрут в БД, если пользователь авторизован
        saved_route_id = None
        if result.get('success') and result.get('route'):
            route_data = result['route']
            
            # Формируем заголовок маршрута
            route_title = f"Маршрут по {city_name or 'городу'} - {', '.join(visit_categories[:3])}"
            if len(visit_categories) > 3:
                route_title += f" и др."
            
            # Сохраняем в БД если пользователь авторизован
            if request.user.is_authenticated:
                try:
                    from core.models import Route
                    
                    route = Route.objects.create(
                        user=request.user,
                        title=route_title,
                        start_point_lat=start_lat,
                        start_point_lon=start_lon,
                        start_point_address=start_address,
                        end_point_lat=route_data['end_point']['lat'],
                        end_point_lon=route_data['end_point']['lon'],
                        end_point_address=route_data['end_point'].get('address', route_data['end_point'].get('name', 'Конечная точка')),
                        end_type=end_type,
                        total_distance=route_data['total_distance'],
                        total_duration=route_data['total_duration'],
                        walking_time=walking_time,
                        city_name=city_name,
                        categories=visit_categories,
                        route_data=route_data
                    )
                    saved_route_id = route.id
                    logger.info(f"✅ Маршрут сохранен в БД с ID: {saved_route_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка при сохранении маршрута: {e}", exc_info=True)
            else:
                logger.info("👤 Пользователь не авторизован - маршрут не сохранен")
        
        # Добавляем информацию о сохранении в ответ
        result['route_saved'] = saved_route_id is not None
        result['route_id'] = saved_route_id
        result['user_authenticated'] = request.user.is_authenticated
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Ошибка в API маршрута: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def save_route_api(request):
    """API для ручного сохранения маршрута"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'requires_login': True,
            'error': 'Необходимо авторизоваться для сохранения маршрутов'
        })
    
    try:
        data = json.loads(request.body)
        route_data = data.get('route_data')
        city_name = data.get('city_name', '')
        walking_time = int(data.get('walking_time', 60))
        visit_categories = data.get('visit_categories', [])
        
        if not route_data:
            return JsonResponse({'success': False, 'error': 'Нет данных маршрута'})
        
        from core.models import Route
        
        # Формируем заголовок маршрута
        route_title = f"Маршрут по {city_name or 'городу'} - {', '.join(visit_categories[:3])}"
        if len(visit_categories) > 3:
            route_title += f" и др."
        
        route = Route.objects.create(
            user=request.user,
            title=route_title,
            start_point_lat=route_data['start_point']['lat'],
            start_point_lon=route_data['start_point']['lon'],
            start_point_address=route_data['start_point'].get('address', 'Начальная точка'),
            end_point_lat=route_data['end_point']['lat'],
            end_point_lon=route_data['end_point']['lon'],
            end_point_address=route_data['end_point'].get('address', route_data['end_point'].get('name', 'Конечная точка')),
            end_type=request.POST.get('end_type', 'start'),
            total_distance=route_data['total_distance'],
            total_duration=route_data['total_duration'],
            walking_time=walking_time,
            city_name=city_name,
            categories=visit_categories,
            route_data=route_data
        )
        
        logger.info(f"✅ Маршрут сохранен пользователем {request.user.username} с ID: {route.id}")
        
        return JsonResponse({
            'success': True,
            'route_id': route.id,
            'message': 'Маршрут успешно сохранен'
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении маршрута: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)})

from django.contrib.auth.decorators import login_required

@login_required
def delete_route_api(request, route_id):
    """Удаление сохраненного маршрута"""
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'})
    
    try:
        from core.models import Route
        route = Route.objects.get(id=route_id, user=request.user)
        route.delete()
        
        logger.info(f"✅ Маршрут {route_id} удален пользователем {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Маршрут удален'
        })
    except Route.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Маршрут не найден'
        })
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении маршрута: {e}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

