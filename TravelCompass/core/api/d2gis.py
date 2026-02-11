import requests
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

def get_city_coordinates_from_2gis(city_name):
    """
    Получаем точные координаты города через 2GIS API
    """
    if not city_name or city_name.strip() == "":
        return None
    
    try:
        query_variants = [
            f"{city_name}, Россия",
            city_name,
            f"город {city_name}"
        ]
        
        city_data = None
        
        for query_variant in query_variants:
            try:
                response = requests.get(
                    "https://catalog.api.2gis.com/3.0/items",
                    params={
                        "key": settings.DG2IS_API_KEY,
                        "q": query_variant,
                        "fields": "items.point,items.name,items.full_name,items.type",
                        "page_size": 5,
                        "locale": "ru_RU",
                    },
                    timeout=10
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                items = data.get("result", {}).get("items", [])
                
                if not items:
                    continue
                
                for item in items:
                    item_type = item.get("type", "").lower()
                    if "city" in item_type or "settlement" in item_type or "town" in item_type:
                        point = item.get("point")
                        if point:
                            lat = point.get("lat")
                            lon = point.get("lon")
                            
                            if lat is not None and lon is not None:
                                logger.info(f"Найден город '{city_name}' как '{query_variant}': lat={lat}, lon={lon}")
                                city_data = {
                                    "lat": lat,
                                    "lon": lon,
                                    "name": item.get("full_name", city_name),
                                    "original_name": city_name
                                }
                                break
                
                if city_data:
                    break
                    
            except Exception as e:
                logger.warning(f"Ошибка варианта запроса '{query_variant}': {e}")
                continue
        
        if not city_data:
            try:
                response = requests.get(
                    "https://catalog.api.2gis.com/3.0/items/geocode",
                    params={
                        "key": settings.DG2IS_API_KEY,
                        "q": f"{city_name}, Россия",
                        "fields": "items.point,items.name",
                        "page_size": 1,
                        "locale": "ru_RU",
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("result", {}).get("items", [])
                    
                    if items:
                        item = items[0]
                        point = item.get("point")
                        if point:
                            lat = point.get("lat")
                            lon = point.get("lon")
                            
                            if lat is not None and lon is not None:
                                logger.info(f"Геокодирование нашло '{city_name}': lat={lat}, lon={lon}")
                                city_data = {
                                    "lat": lat,
                                    "lon": lon,
                                    "name": item.get("name", city_name),
                                    "original_name": city_name
                                }
            except Exception as e:
                logger.error(f"Ошибка геокодирования: {e}")
        
        if not city_data:
            logger.warning(f"Город '{city_name}' не найден ни одним методом")
            return None
        
        return city_data
        
    except Exception as e:
        logger.error(f"Общая ошибка получения координат города '{city_name}': {e}")
        return None

def search_places_in_city_using_coordinates(query="", city_data=None, category=""):
    """
    Ищем места в городе используя уже полученные координаты
    """
    if not city_data:
        logger.error("Нет данных города для поиска")
        return []
    
    city_name = city_data.get("original_name", "город")
    city_lat = city_data.get("lat")
    city_lon = city_data.get("lon")
    
    if city_lat is None or city_lon is None:
        logger.error(f"Нет координат для города '{city_name}'")
        return []
    
    search_query = query.strip() if query and query.strip() else ""
    
    CATEGORY_MAP = {
        "cafe": "кафе",
        "park": "парк",
        "restaurant": "ресторан",
    }
    
    if category and category in CATEGORY_MAP:
        if not search_query:
            search_query = CATEGORY_MAP[category]
        else:
            # Убираем дублирование, если пользователь уже ввел то же слово
            if CATEGORY_MAP[category] not in search_query.lower():
                search_query = f"{search_query} {CATEGORY_MAP[category]}"
    
    if not search_query:
        search_query = city_name
    else:
        search_query = f"{search_query} {city_name}"
    
    try:
        params = {
            "key": settings.DG2IS_API_KEY,
            "q": search_query,
            "fields": "items.point,items.name,items.address_name,items.rubrics,items.type",
            "page_size": 10,
            "locale": "ru_RU",
            "sort": "relevance",
        }
        
        logger.info(f"Поиск мест для города '{city_name}'")
        logger.info(f"Запрос: '{search_query}', категория: '{category}'")
        
        response = requests.get(
            "https://catalog.api.2gis.com/3.0/items",
            params=params,
            timeout=15
        )
        
        logger.info(f"Статус API: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"2GIS API ошибка: {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get("meta", {}).get("code") != 200:
            error_msg = data.get("meta", {}).get("error", {}).get("message", "Unknown error")
            logger.error(f"API вернул ошибку: {error_msg}")
            return []
        
        places = []
        items = data.get("result", {}).get("items", [])
        total = data.get("result", {}).get("total", 0)
        
        logger.info(f"Всего найдено по API: {total} элементов, возвращено: {len(items)}")
        
        for item in items:
            point = item.get("point")
            if not point:
                continue
            
            place_lat = point.get("lat")
            place_lon = point.get("lon")
            
            if place_lat is None or place_lon is None:
                continue
            
            rubrics = item.get("rubrics", [])
            rubric_names = [r.get("name", "") for r in rubrics if isinstance(r, dict)]
            
            if category:
                item_type = item.get("type", "").lower()
                rubric_text = " ".join(rubric_names).lower()
                item_name = item.get("name", "").lower()
                
                is_cafe = category == "cafe" and (
                    "кафе" in rubric_text or 
                    "кофейня" in rubric_text or 
                    "кафе" in item_type or
                    "кофейня" in item_name
                )
                is_park = category == "park" and (
                    "парк" in rubric_text or 
                    "сквер" in rubric_text or 
                    "парк" in item_type or
                    "парк" in item_name or
                    "сквер" in item_name
                )
                is_restaurant = category == "restaurant" and (
                    "ресторан" in rubric_text or 
                    "ресторан" in item_type or
                    "ресторан" in item_name
                )
                
                if category == "cafe" and not is_cafe:
                    continue
                elif category == "park" and not is_park:
                    continue
                elif category == "restaurant" and not is_restaurant:
                    continue
            
            places.append({
                "name": item.get("name", "Без названия"),
                "address": item.get("address_name", ""),
                "lat": place_lat,
                "lon": place_lon,
                "type": item.get("type", ""),
                "rubrics": rubric_names,
            })
        
        logger.info(f"После фильтрации осталось {len(places)} мест")
        
        return places
        
    except Exception as e:
        logger.error(f"Ошибка поиска мест в городе '{city_name}': {e}", exc_info=True)
        return []

def search_places(query="", city="", category=""):
    """
    Основная функция поиска: получаем координаты города, потом ищем места
    """
    if not city or city.strip() == "":
        logger.info("Город не указан, возвращаем пустой результат")
        return [], None
    
    city_data = get_city_coordinates_from_2gis(city)
    if not city_data:
        logger.error(f"Не удалось получить координаты города '{city}'")
        return [], None
    
    logger.info(f"Получены координаты для '{city}': lat={city_data['lat']}, lon={city_data['lon']}")
    
    places = search_places_in_city_using_coordinates(
        query=query,
        city_data=city_data,
        category=category
    )
    
    return places, city_data
import math
import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

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

def parse_linestring(ls):
    coords = []
    ls = ls.replace("LINESTRING(", "").replace(")", "")
    for pair in ls.split(","):
        lon, lat = pair.strip().split()
        coords.append({
            "lat": float(lat),
            "lon": float(lon)
        })
    return coords

def calculate_route_osrm(points):
    """Используем бесплатный OSRM для построения пеших маршрутов по дорогам"""
    if len(points) < 2:
        return {"success": False, "error": "Недостаточно точек"}
    
    try:
        # Формируем URL для OSRM (пеший маршрут)
        coords_str = ";".join([f"{lon},{lat}" for lat, lon in points])
        url = f"http://router.project-osrm.org/route/v1/walking/{coords_str}"
        
        params = {
            "overview": "full",      # Полная геометрия маршрута
            "geometries": "geojson", # Формат GeoJSON
            "steps": "false",        # Не нужны детальные шаги
            "alternatives": "false"  # Только один маршрут
        }
        
        logger.info(f"Запрос к OSRM для {len(points)} точек: {coords_str[:100]}...")
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                
                # Конвертируем из формата GeoJSON [lon, lat] в наш формат {lat, lon}
                route_coordinates = []
                geometry = route["geometry"]["coordinates"]
                
                for coords in geometry:
                    if len(coords) >= 2:
                        lon, lat = coords[0], coords[1]
                        route_coordinates.append({
                            "lat": lat,
                            "lon": lon
                        })
                
                logger.info(f"OSRM построил маршрут: {len(route_coordinates)} точек, {route['distance']:.0f}м, {route['duration']:.0f}с")
                
                return {
                    "success": True,
                    "distance": route["distance"],      # в метрах
                    "duration": route["duration"],      # в секундах
                    "route_coordinates": route_coordinates
                }
        
        logger.error(f"OSRM ошибка {response.status_code}: {response.text[:200]}")
        return {"success": False, "error": f"OSRM ошибка {response.status_code}"}
        
    except Exception as e:
        logger.error(f"Ошибка OSRM: {e}")
        return {"success": False, "error": str(e)}

def calculate_route_2gis(points):
    """Основная функция для построения маршрутов с fallback на OSRM"""
    if len(points) < 2:
        return {"success": False, "error": "Недостаточно точек"}
    
    # Сначала пробуем OSRM (бесплатный, работает по дорогам)
    logger.info(f"Пробуем построить пеший маршрут через OSRM для {len(points)} точек")
    osrm_result = calculate_route_osrm(points)
    
    if osrm_result["success"]:
        logger.info("Успешно использован OSRM для построения маршрута по дорогам")
        return osrm_result
    
    # Если OSRM не сработал, пробуем 2GIS (но скорее всего он тоже не сработает)
    logger.info("OSRM не сработал, пробуем 2GIS...")
    try:
        # Упрощенный формат для 2GIS
        points_str = ";".join([f"{lon},{lat}" for lat, lon in points])
        
        params = {
            "key": settings.DG2IS_API_KEY,
            "points": points_str,
            "type": "pedestrian",
            "locale": "ru_RU"
        }
        
        logger.info(f"Запрос к 2GIS Routing API: {points_str[:100]}...")
        
        response = requests.get(
            "https://routing.api.2gis.com/get_route",
            params=params,
            timeout=15
        )
        
        logger.info(f"2GIS API ответ: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"2GIS API успешно")
            
            # Обработка ответа 2GIS
            route_coordinates = []
            total_distance = 0
            total_duration = 0
            
            if "result" in data and data["result"]:
                route = data["result"][0]
                total_distance = route.get("total_distance", 0)
                total_duration = route.get("total_duration", 0)
                
                # Парсим геометрию
                geometry = route.get("geometry")
                if geometry:
                    route_coordinates = parse_linestring(geometry)
            
            if route_coordinates:
                logger.info(f"2GIS построил маршрут: {len(route_coordinates)} точек")
                return {
                    "success": True,
                    "distance": total_distance,
                    "duration": total_duration,
                    "route_coordinates": route_coordinates
                }
        
        # Если 2GIS не сработал, возвращаем упрощенный маршрут
        logger.warning("Ни OSRM, ни 2GIS не сработали, используем упрощенный маршрут")
        return create_simple_route(points)
            
    except Exception as e:
        logger.error(f"Ошибка 2GIS Routing API: {e}")
        # Возвращаем упрощенный маршрут
        return create_simple_route(points)

def create_simple_route(points):
    """Создание упрощенного маршрута (по прямой) - используется как последнее средство"""
    route_coordinates = []
    total_distance = 0
    
    for i, (lat, lon) in enumerate(points):
        route_coordinates.append({"lat": lat, "lon": lon})
        if i > 0:
            prev_lat, prev_lon = points[i-1]
            total_distance += calculate_distance(prev_lat, prev_lon, lat, lon)
    
    logger.warning(f"Используем упрощенный маршрут (по прямой): {total_distance:.0f}м")
    
    return {
        "success": True,
        "distance": total_distance,
        "duration": total_distance / 1.4,  # Пешком ~5 км/ч
        "route_coordinates": route_coordinates
    }
