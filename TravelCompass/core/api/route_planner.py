# core/api/route_planner.py
import requests
from django.conf import settings
import logging
import math
from typing import List, Dict, Tuple, Optional
from core.api.d2gis import calculate_route_2gis

logger = logging.getLogger(__name__)

WALKING_SPEED = 1.4

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Рассчитывает расстояние между двумя точками в метрах (формула гаверсинусов)"""
    R = 6371000
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def find_places_in_radius(center_lat: float, center_lon: float, radius: float, 
                         categories: List[str], city_name: str = None) -> List[Dict]:
    """
    Находит места в указанном радиусе от центра
    """
    try:
        logger.info("=" * 60)
        logger.info(f"ПОИСК МЕСТ В РАДИУСЕ {radius}м")
        logger.info(f"Центр: {center_lat}, {center_lon}")
        logger.info(f"Категории: {categories}")
        logger.info(f"Город: {city_name}")
        logger.info("=" * 60)
        
        category_map = {
            'cafe': 'кафе',
            'restaurant': 'ресторан',
            'park': 'парк',
            'museum': 'музей',
            'theater': 'театр',
            'cinema': 'кинотеатр',
            'shop': 'магазин',
            'attraction': 'достопримечательность'
        }
        
        all_places = []

        city_coords = None
        if city_name:
            try:
                response = requests.get(
                    "https://catalog.api.2gis.com/3.0/items/geocode",
                    params={
                        "key": settings.DG2IS_API_KEY,
                        "q": city_name,
                        "page_size": 1,
                        "locale": "ru_RU",
                    },
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("result", {}).get("items", [])
                    if items:
                        point = items[0].get("point")
                        if point:
                            city_coords = (point.get("lat"), point.get("lon"))
                            logger.info(f"✅ Найдены координаты города {city_name}: {city_coords}")
            except Exception as e:
                logger.error(f"Ошибка геокодирования города: {e}")
        
        for category in categories:
            if category in category_map:
                search_term = category_map[category]
                logger.info(f"\n--- Поиск категории: {category} ({search_term}) ---")
                
                found = False
                
                if city_name and not found:
                    try:
                        params = {
                            "key": settings.DG2IS_API_KEY,
                            "q": f"{search_term} {city_name}",
                            "fields": "items.point,items.name,items.address_name",
                            "page_size": 20,
                            "locale": "ru_RU",
                            "sort": "relevance",
                        }
                        
                        logger.info(f"Запрос 1 (по городу): {params['q']}")
                        response = requests.get(
                            "https://catalog.api.2gis.com/3.0/items",
                            params=params,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get("result", {}).get("items", [])
                            
                            if items:
                                found = True
                                logger.info(f"✅ Найдено {len(items)} мест по городу")
                                
                                for item in items:
                                    point = item.get("point")
                                    if point:
                                        place_lat = point.get("lat")
                                        place_lon = point.get("lon")
                                        
                                        if place_lat and place_lon:
                                            distance = calculate_distance(
                                                center_lat, center_lon,
                                                place_lat, place_lon
                                            )
                                            
                                            place = {
                                                "name": item.get("name", "Без названия"),
                                                "address": item.get("address_name", ""),
                                                "lat": place_lat,
                                                "lon": place_lon,
                                                "category": category,
                                                "distance": distance,
                                            }
                                            all_places.append(place)
                                            logger.info(f"  ✅ {place['name']} - {distance:.0f}м")
                    except Exception as e:
                        logger.error(f"Ошибка в стратегии 1: {e}")
                
                if city_coords and not found:
                    try:
                        params = {
                            "key": settings.DG2IS_API_KEY,
                            "q": search_term,
                            "point": f"{city_coords[1]},{city_coords[0]}",
                            "radius": min(radius, 5000),
                            "fields": "items.point,items.name,items.address_name",
                            "page_size": 20,
                            "locale": "ru_RU",
                            "sort": "distance",
                        }
                        
                        logger.info(f"Запрос 2 (по координатам города): {params}")
                        response = requests.get(
                            "https://catalog.api.2gis.com/3.0/items",
                            params=params,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get("result", {}).get("items", [])
                            
                            if items:
                                found = True
                                logger.info(f"✅ Найдено {len(items)} мест по координатам города")
                                
                                for item in items:
                                    point = item.get("point")
                                    if point:
                                        place_lat = point.get("lat")
                                        place_lon = point.get("lon")
                                        
                                        if place_lat and place_lon:
                                            distance = calculate_distance(
                                                center_lat, center_lon,
                                                place_lat, place_lon
                                            )
                                            
                                            if distance <= radius:
                                                place = {
                                                    "name": item.get("name", "Без названия"),
                                                    "address": item.get("address_name", ""),
                                                    "lat": place_lat,
                                                    "lon": place_lon,
                                                    "category": category,
                                                    "distance": distance,
                                                }
                                                all_places.append(place)
                                                logger.info(f"  ✅ {place['name']} - {distance:.0f}м")
                    except Exception as e:
                        logger.error(f"Ошибка в стратегии 2: {e}")
        
        unique_places = {}
        for place in all_places:
            coord_key = f"{place['lat']:.6f},{place['lon']:.6f}"
            if coord_key not in unique_places:
                unique_places[coord_key] = place
        
        unique_places_list = list(unique_places.values())
        unique_places_list.sort(key=lambda x: x['distance'])
        
        logger.info("\n" + "=" * 60)
        logger.info(f"ИТОГО: Найдено {len(unique_places_list)} уникальных мест")
        
        if not unique_places_list:
            logger.warning("⚠️ API НЕ ВЕРНУЛ ДАННЫХ! ИСПОЛЬЗУЕМ ТЕСТОВЫЕ МЕСТА")
            return get_test_places(center_lat, center_lon, categories)
        
        return unique_places_list[:10]
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        # В случае ошибки - тестовые данные
        return get_test_places(center_lat, center_lon, categories)

def plan_optimal_route(start_point: Tuple[float, float],
                      end_type: str,
                      end_point: Optional[Tuple[float, float]] = None,
                      end_category: Optional[str] = None,
                      walking_time: int = 60,
                      visit_categories: List[str] = None,
                      radius: float = 5000,
                      city_name: str = None) -> Dict:
    """
    Планирует оптимальный пеший маршрут
    """
    try:
        # ============= ОТЛАДКА =============
        logger.info("=" * 80)
        logger.info("ФУНКЦИЯ plan_optimal_route ВЫЗВАНА!")
        logger.info(f"Параметры:")
        logger.info(f"  start_point: {start_point}")
        logger.info(f"  end_type: {end_type}")
        logger.info(f"  end_point: {end_point}")
        logger.info(f"  end_category: {end_category}")
        logger.info(f"  walking_time: {walking_time}")
        logger.info(f"  visit_categories: {visit_categories}")
        logger.info(f"  radius: {radius}")
        logger.info(f"  city_name: {city_name}")
        logger.info("=" * 80)
        # ============= ОТЛАДКА =============
        
        start_lat, start_lon = start_point
        
        # 1. Определяем конечную точку
        if end_type == "start":
            # Круговой маршрут - возвращаемся в начало
            end_lat, end_lon = start_lat, start_lon
            end_point_name = "Начальная точка (круговой маршрут)"
        elif end_type == "specific" and end_point:
            end_lat, end_lon = end_point
            end_point_name = "Выбранная точка"
        elif end_type == "category" and end_category:
            places = find_places_in_radius(
                start_lat, start_lon, radius,
                [end_category], city_name
            )
            
            if not places:
                return {"success": False, "error": f"Не найдено мест категории '{end_category}' в радиусе"}
            
            end_place = places[0]
            end_lat, end_lon = end_place["lat"], end_place["lon"]
            end_point_name = f"{end_place['name']}"
        else:
            return {"success": False, "error": "Неверно указана конечная точка"}
        
        # 2. Находим интересные места для посещения
        intermediate_places = []
        if visit_categories:

            logger.info("🔵🔵🔵 ИСПОЛЬЗУЕМ РЕАЛЬНЫЙ API 2GIS 🔵🔵🔵")
            intermediate_places = find_places_in_radius(
                start_lat, start_lon, radius,
                visit_categories, city_name
            )
    
            logger.info(f"✅ Найдено РЕАЛЬНЫХ мест: {len(intermediate_places)}")
            for i, place in enumerate(intermediate_places[:5]):
                logger.info(f"  РЕАЛЬНОЕ {i+1}: {place['name']} - {place['distance']:.0f}м")
        
        # 3. Ограничение точек по времени (1 точка на каждые 30 минут)
        points_limit = max(1, walking_time // 30)
        logger.info(f"Берём {points_limit} точек для маршрута")
        intermediate_places = intermediate_places[:points_limit]
        
        # 4. Оптимизируем порядок посещения
        optimized_points = [] 
        if intermediate_places:
            current_lat, current_lon = start_lat, start_lon
            remaining_places = intermediate_places.copy()
    
            logger.info(f"Начинаем оптимизацию {len(remaining_places)} точек")
    
            while remaining_places:
                nearest_idx = 0
                nearest_dist = float('inf')
        
                for i, place in enumerate(remaining_places):
                    dist = calculate_distance(
                        current_lat, current_lon,
                        place["lat"], place["lon"]
                    )
            
                    if dist < nearest_dist:
                        nearest_dist = dist
                        nearest_idx = i
        
                next_place = remaining_places.pop(nearest_idx)
                optimized_points.append(next_place)
                logger.info(f"  Добавлена точка {len(optimized_points)}: {next_place['name']} - {nearest_dist:.0f}м")
                current_lat, current_lon = next_place["lat"], next_place["lon"]
    
            logger.info(f"Оптимизировано {len(optimized_points)} точек")
        else:
            logger.info("Нет промежуточных точек для оптимизации")
        
        # 5. Строим маршрут в зависимости от типа
        all_points = [(start_lat, start_lon)]  # Начало
        
        # Добавляем промежуточные точки
        for place in optimized_points:
            all_points.append((place["lat"], place["lon"]))
        
        # Добавляем конечную точку
        if end_type == "start":
            # Круговой маршрут - возвращаемся в начало
            all_points.append((start_lat, start_lon))
        else:
            all_points.append((end_lat, end_lon))
        
        # 6. Рассчитываем маршрут
        logger.info(f"Строим маршрут из {len(all_points)} точек")
        
        if len(all_points) == 2 and all_points[0] == all_points[1]:
            # Круговой маршрут из одной точки
            route_result = {
                "success": True,
                "distance": 0,
                "duration": 0,
                "route_coordinates": [{"lat": start_lat, "lon": start_lon}]
            }
        else:
            route_result = calculate_route_2gis(all_points)
            
            if not route_result["success"]:
                # Если API не сработало, используем упрощенный маршрут
                route_coordinates = []
                for lat, lon in all_points:
                    route_coordinates.append({"lat": lat, "lon": lon})
                
                total_distance = 0
                for i in range(len(all_points) - 1):
                    total_distance += calculate_distance(
                        all_points[i][0], all_points[i][1],
                        all_points[i+1][0], all_points[i+1][1]
                    )
                
                route_result = {
                    "success": True,
                    "distance": total_distance,
                    "duration": total_distance / WALKING_SPEED,
                    "route_coordinates": route_coordinates
                }
        
        # 7. Формируем результат
        logger.info(f"Найдено {len(optimized_points)} промежуточных точек для маршрута")
        
        return {
            "success": True,
            "route": {
                "start_point": {
                    "lat": start_lat,
                    "lon": start_lon,
                    "address": "Начальная точка"
                },
                "end_point": {
                    "lat": end_lat if end_type != "start" else start_lat,
                    "lon": end_lon if end_type != "start" else start_lon,
                    "name": end_point_name,
                    "address": end_point_name
                },
                "intermediate_points": optimized_points,
                "total_distance": route_result["distance"],
                "total_duration": route_result["duration"],
                "route_coordinates": route_result["route_coordinates"],
                "categories": visit_categories or []
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка планирования маршрута: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    

# Временная функция для тестирования маршрутов
def get_test_places(center_lat, center_lon, categories):
    """Возвращает тестовые места для проверки отображения"""
    test_places = []
    
    test_data = [
        (0.002, 0.001, "Кафе Центральное", "cafe", "ул. Ленина, 10"),
        (-0.001, 0.003, "Парк Горького", "park", "ул. Парковая, 1"),
        (0.003, -0.001, "Ресторан Волга", "restaurant", "наб. реки, 15"),
        (-0.002, -0.002, "Музей искусств", "museum", "пл. Искусств, 5"),
        (0.001, -0.002, "Театр драмы", "theater", "ул. Театральная, 7"),
    ]
    
    for lat_off, lon_off, name, cat, addr in test_data:
        if cat in categories:
            place = {
                "name": name,
                "address": addr,
                "lat": center_lat + lat_off,
                "lon": center_lon + lon_off,
                "category": cat,
                "distance": calculate_distance(center_lat, center_lon, center_lat + lat_off, center_lon + lon_off),
            }
            test_places.append(place)
    
    return test_places