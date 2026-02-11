# core/api/route_planner.py
import requests
from django.conf import settings
import logging
import math
from typing import List, Dict, Tuple, Optional
from core.api.d2gis import calculate_route_2gis

logger = logging.getLogger(__name__)

# Скорость пешехода в м/с (примерно 5 км/ч)
WALKING_SPEED = 1.4

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Рассчитывает расстояние между двумя точками в метрах (формула гаверсинусов)"""
    R = 6371000  # радиус Земли в метрах
    
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
        # Преобразуем категории в поисковые запросы
        category_map = {
            'cafe': 'кафе кофейня',
            'restaurant': 'ресторан',
            'park': 'парк сквер',
            'museum': 'музей выставка галерея',
            'theater': 'театр',
            'cinema': 'кинотеатр кино',
            'shop': 'магазин торговый центр',
            'attraction': 'достопримечательность памятник'
        }
        
        all_places = []
        
        # Ищем места для каждой категории
        for category in categories:
            if category in category_map:
                search_terms = category_map[category].split()
                
                for term in search_terms:
                    try:
                        params = {
                            "key": settings.DG2IS_API_KEY,
                            "q": f"{term} {city_name}" if city_name else term,
                            "fields": "items.point,items.name,items.address_name,items.rubrics",
                            "page_size": 20,
                            "locale": "ru_RU",
                            "sort": "distance",
                        }
                        
                        # Если есть координаты центра, ищем в радиусе
                        if center_lat and center_lon:
                            params["point"] = f"{center_lon},{center_lat}"
                            params["radius"] = int(radius)
                        
                        response = requests.get(
                            "https://catalog.api.2gis.com/3.0/items",
                            params=params,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            items = data.get("result", {}).get("items", [])
                            
                            for item in items:
                                point = item.get("point")
                                if point:
                                    place_lat = point.get("lat")
                                    place_lon = point.get("lon")
                                    
                                    if place_lat and place_lon:
                                        # Проверяем расстояние
                                        distance = calculate_distance(
                                            center_lat, center_lon,
                                            place_lat, place_lon
                                        )
                                        
                                        if distance <= radius:
                                            place = {
                                                "name": item.get("name", ""),
                                                "address": item.get("address_name", ""),
                                                "lat": place_lat,
                                                "lon": place_lon,
                                                "category": category,
                                                "distance": distance
                                            }
                                            all_places.append(place)
                    
                    except Exception as e:
                        logger.error(f"Ошибка поиска для категории {category}: {e}")
                        continue
        
        # Убираем дубликаты (места с одинаковыми координатами)
        unique_places = []
        seen_coords = set()
        
        for place in all_places:
            coord_key = f"{place['lat']:.6f},{place['lon']:.6f}"
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_places.append(place)
        
        # Сортируем по расстоянию
        unique_places.sort(key=lambda x: x['distance'])
        
        logger.info(f"Найдено {len(unique_places)} уникальных мест в радиусе {radius}м")
        return unique_places[:15]  # Ограничиваем количество точек
        
    except Exception as e:
        logger.error(f"Ошибка поиска мест в радиусе: {e}")
        return []

import requests
from django.conf import settings

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
        start_lat, start_lon = start_point
        
        # 1. Определяем конечную точку
        if end_type == "start":
            # Круговой маршрут - возвращаемся в начало
            end_lat, end_lon = start_lat, start_lon
            end_point_name = "Начальная точка"
        elif end_type == "specific" and end_point:
            # Конкретная точка
            end_lat, end_lon = end_point
            end_point_name = "Выбранная точка"
        elif end_type == "category" and end_category:
            # Ищем ближайшее заведение указанной категории
            places = find_places_in_radius(
                start_lat, start_lon, radius,
                [end_category], city_name
            )
            
            if not places:
                return {"success": False, "error": f"Не найдено мест категории '{end_category}' в радиусе"}
            
            # Берем ближайшее место
            end_place = places[0]
            end_lat, end_lon = end_place["lat"], end_place["lon"]
            end_point_name = end_place["name"]
        else:
            return {"success": False, "error": "Неверно указана конечная точка"}
        
        # 2. Находим интересные места для посещения
        if visit_categories:
            intermediate_places = find_places_in_radius(
                start_lat, start_lon, radius,
                visit_categories, city_name
            )
        else:
            intermediate_places = []
        
        # 3. Ограничиваем количество точек на основе времени
        max_points = min(len(intermediate_places), max(3, walking_time // 30))
        intermediate_places = intermediate_places[:max_points]
        # защита от маршрута в ту же точку
        if end_lat == start_lat and end_lon == start_lon:
            return {
                "success": False,
                "error": "Начальная и конечная точка совпадают"
            }

        if not intermediate_places:
            # Если нет промежуточных точек, строим прямой маршрут
            route_result = calculate_route_2gis([
                (start_lat, start_lon),
                (end_lat, end_lon)
            ])
            
            if route_result["success"]:
                return {
                    "success": True,
                    "route": {
                        "start_point": {"lat": start_lat, "lon": start_lon},
                        "end_point": {"lat": end_lat, "lon": end_lon, "name": end_point_name},
                        "intermediate_points": [],
                        "total_distance": route_result["distance"],
                        "total_duration": route_result["duration"],
                        "route_coordinates": route_result["route_coordinates"],
                        "categories": visit_categories or []
                    }
                }
            else:
                return {"success": False, "error": "Не удалось построить маршрут"}
        
        # 4. Оптимизируем порядок посещения (простой алгоритм - ближайший сосед)
        optimized_points = []
        current_lat, current_lon = start_lat, start_lon
        remaining_places = intermediate_places.copy()
        
        while remaining_places:
            # Находим ближайшую точку
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
            
            # Добавляем найденную точку
            nearest_place = remaining_places.pop(nearest_idx)
            optimized_points.append(nearest_place)
            current_lat, current_lon = nearest_place["lat"], nearest_place["lon"]
        
        # 5. Строим маршрут через все точки
        all_points = [(start_lat, start_lon)]
        for place in optimized_points:
            all_points.append((place["lat"], place["lon"]))
        all_points.append((end_lat, end_lon))
        
        # 6. Рассчитываем маршрут через 2GIS API
        route_result = calculate_route_2gis(all_points)
        
        if not route_result["success"]:
            # Если API не сработало, используем упрощенный маршрут
            route_coordinates = []
            for lat, lon in all_points:
                route_coordinates.append({"lat": lat, "lon": lon})
            
            # Приблизительно оцениваем расстояние и время
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
        return {
            "success": True,
            "route": {
                "start_point": {
                    "lat": start_lat,
                    "lon": start_lon,
                    "address": "Начальная точка"
                },
                "end_point": {
                    "lat": end_lat,
                    "lon": end_lon,
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