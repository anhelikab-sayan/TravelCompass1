import requests
from django.conf import settings


def geocode_city(city_name):
    response = requests.get(
        "https://catalog.api.2gis.com/3.0/items/geocode",
        params={
            "key": settings.DG2IS_API_KEY,
            "q": city_name,
            "fields": "items.point,items.name,items.full_name",
            "page_size": 1,
            "locale": "ru_RU",  # можно en_US
        },
        timeout=10
    )

    data = response.json()
    items = data.get("result", {}).get("items", [])

    if not items:
        return None

    point = items[0].get("point")
    if not point:
        return None

    return {
        "lat": point["lat"],
        "lon": point["lon"],
        "name": items[0].get("full_name", city_name),
    }

def search_places(query="", city="", category=""):
    city_data = geocode_city(city)

    if not city_data:
        return [], None

    search_parts = []

    if query:
        search_parts.append(query)

    CATEGORY_MAP = {
        "cafe": "кафе",
        "park": "парк",
        "restaurant": "ресторан",
    }

    if category in CATEGORY_MAP:
        search_parts.append(CATEGORY_MAP[category])

    params = {
        "key": settings.DG2IS_API_KEY,
        "q": " ".join(search_parts) or "*",
        "point": f"{city_data['lon']},{city_data['lat']}",
        "radius": 15000,
        "page_size": 50,
        "type": "branch",
        "fields": "items.point,items.name,items.address_name",
    }

    response = requests.get(
        "https://catalog.api.2gis.com/3.0/items",
        params=params,
        timeout=10
    )

    data = response.json()

    places = []
    for item in data.get("result", {}).get("items", []):
        point = item.get("point")
        if not point:
            continue

        places.append({
            "name": item.get("name", "Без названия"),
            "address": item.get("address_name", ""),
            "lat": point["lat"],
            "lon": point["lon"],
        })

    return places, city_data
