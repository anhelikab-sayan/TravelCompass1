import json
from django.shortcuts import render
from core.api.d2gis import search_places, POPULAR_CITIES


def index(request):
    return render(request, "core/index.html")


def search(request):
    query = request.GET.get("q", "")
    city = request.GET.get("city", "Красноярск")
    category = request.GET.get("category", "")

    places, city_center = search_places(query, city, category)

    context = {
        "places_json": json.dumps(places),
        "query": query,
        "city": city,
        "category": category,
        "cities": POPULAR_CITIES.keys(),
        "city_lat": city_center["lat"],
        "city_lon": city_center["lon"],
    }

    return render(request, "core/search.html", context)
