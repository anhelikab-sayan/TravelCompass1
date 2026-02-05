# d2gis.py - исправленная версия
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
    
    # Формируем поисковый запрос
    search_query = query.strip() if query and query.strip() else ""
    
    # Если указана категория, добавляем к запросу
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
    
    # Если запрос пустой, ищем всё в этом городе
    if not search_query:
        search_query = city_name
    else:
        # Добавляем город к запросу для более точного поиска
        search_query = f"{search_query} {city_name}"
    
    try:
        # ПАРАМЕТРЫ КАК В РАБОЧЕМ ПРИМЕРЕ
        params = {
            "key": settings.DG2IS_API_KEY,
            "q": search_query,
            "fields": "items.point,items.name,items.address_name,items.rubrics,items.type",
            "page_size": 10,  # ИЗМЕНИЛОСЬ: от 1 до 10 согласно ошибке
            "locale": "ru_RU",
            "sort": "relevance",
        }
        
        logger.info(f"Поиск мест для города '{city_name}'")
        logger.info(f"Запрос: '{search_query}', категория: '{category}'")
        logger.info(f"Параметры: {params}")
        
        response = requests.get(
            "https://catalog.api.2gis.com/3.0/items",
            params=params,
            timeout=15
        )
        
        logger.info(f"Статус API: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"2GIS API ошибка: {response.status_code}")
            logger.error(f"Ответ: {response.text[:500]}")
            return []
        
        data = response.json()
        
        # Проверяем на ошибки в ответе
        if data.get("meta", {}).get("code") != 200:
            error_msg = data.get("meta", {}).get("error", {}).get("message", "Unknown error")
            logger.error(f"API вернул ошибку: {error_msg}")
            logger.error(f"Полный ответ: {json.dumps(data, ensure_ascii=False)}")
            return []
        
        # Отладочный вывод
        logger.debug(f"Полный ответ API: {json.dumps(data, ensure_ascii=False)[:1000]}")
        
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
            
            # Получаем рубрики для фильтрации
            rubrics = item.get("rubrics", [])
            rubric_names = [r.get("name", "") for r in rubrics if isinstance(r, dict)]
            
            # Фильтрация по категории (если указана)
            if category:
                item_type = item.get("type", "").lower()
                rubric_text = " ".join(rubric_names).lower()
                item_name = item.get("name", "").lower()
                
                # Проверяем, подходит ли место под категорию
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
        
        # Для отладки - выводим первые 5 мест
        if places:
            for i, place in enumerate(places[:5]):
                logger.info(f"Место {i+1}: {place['name']} - {place['address']}")
                logger.info(f"  Рубрики: {place['rubrics']}")
        
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