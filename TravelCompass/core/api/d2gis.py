import requests
from django.conf import settings

BASE_URL = "https://catalog.api.2gis.com/3.0/items"


def search_places(query, city="Новосибирск", limit=10):
    """
    Поиск мест через API 2ГИС
    """
    params = {
        "q": query,
        "region": city,
        "page_size": limit,
        "key": settings.DG2IS_API_KEY,
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    places = []

    for item in data.get("result", {}).get("items", []):
        point = item.get("point", {})
        places.append({
            "id": item.get("id"),
            "name": item.get("name", "Без названия"),
            "address": item.get("address_name", ""),
            "lat": point.get("lat"),
            "lon": point.get("lon"),
        })

    return places