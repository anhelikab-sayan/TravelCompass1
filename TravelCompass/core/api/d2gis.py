import requests
from django.conf import settings
import logging

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
    
    search_parts = []
    
    if query and query.strip():
        search_parts.append(query.strip())
    
    CATEGORY_MAP = {
        "cafe": "кафе кофейня",
        "park": "парк сквер",
        "restaurant": "ресторан",
    }
    
    if category in CATEGORY_MAP:
        search_parts.append(CATEGORY_MAP[category])
    
    search_query = " ".join(search_parts) if search_parts else "*"
    
    try:
        params = {
            "key": settings.DG2IS_API_KEY,
            "q": search_query,
            "point": f"{city_lon},{city_lat}",
            "radius": 10000,
            "page_size": 30,
            "type": "branch",
            "fields": "items.point,items.name,items.address_name",
            "locale": "ru_RU",
        }
        
        logger.info(f"Поиск мест в городе '{city_name}' с координатами {city_lat},{city_lon}")
        logger.info(f"Запрос: {search_query}")
        
        response = requests.get(
            "https://catalog.api.2gis.com/3.0/items",
            params=params,
            timeout=15
        )
        
        if response.status_code != 200:
            logger.error(f"2GIS API ошибка при поиске мест: {response.status_code}")
            logger.error(f"Ответ: {response.text[:200]}")
            return []
        
        data = response.json()
        places = []
        
        for item in data.get("result", {}).get("items", []):
            point = item.get("point")
            if not point:
                continue
            
            place_lat = point.get("lat")
            place_lon = point.get("lon")
            
            if place_lat is None or place_lon is None:
                continue
            
            places.append({
                "name": item.get("name", "Без названия"),
                "address": item.get("address_name", ""),
                "lat": place_lat,
                "lon": place_lon,
            })
        
        logger.info(f"Найдено {len(places)} мест в городе '{city_name}'")
        return places
        
    except Exception as e:
        logger.error(f"Ошибка поиска мест в городе '{city_name}': {e}")
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
    
    logger.info(f"Получены координаты для '{city}': lat={city_data['lat']}, lon={city_data['lon']}, тип lat: {type(city_data['lat'])}, тип lon: {type(city_data['lon'])}")
    
    places = search_places_in_city_using_coordinates(
        query=query,
        city_data=city_data,
        category=category
    )
    
    return places, city_data