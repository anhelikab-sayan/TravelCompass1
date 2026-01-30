import requests
from django.conf import settings

POPULAR_CITIES = {
    "Красноярск": {"lat": 56.0153, "lon": 92.8932},
    "Москва": {"lat": 55.7558, "lon": 37.6173},
    "Санкт-Петербург": {"lat": 59.9343, "lon": 30.3351},
    "Новосибирск": {"lat": 55.0084, "lon": 82.9357},
    "Екатеринбург": {"lat": 56.8389, "lon": 60.6057},
}


def get_city_center(city):
    return POPULAR_CITIES.get(city, POPULAR_CITIES["Красноярск"])


def search_places(query="", city="Красноярск", category=""):
    city_data = get_city_center(city)

    params = {
        "key": settings.DG2IS_API_KEY,
        "point": f"{city_data['lon']},{city_data['lat']}",
        "radius": 15000,
        "page_size": 20,
        "fields": "items.point,items.name,items.address_name",
    }

    if query:
        params["q"] = query

    if category:
        params["type"] = category

    response = requests.get(
        "https://catalog.api.2gis.com/3.0/items",
        params=params,
        timeout=10,
    )

    data = response.json()

    places = []
    for item in data.get("result", {}).get("items", []):
        point = item.get("point")
        if not point:
            continue

        places.append({
            "name": item["name"],
            "address": item.get("address_name", ""),
            "lat": point["lat"],
            "lon": point["lon"],
        })

    return places, city_data
