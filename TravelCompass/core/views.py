# core/views.py
import json
from django.shortcuts import render
from core.api.d2gis import search_places


def search_view(request):
    query = request.GET.get("q", "")
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")

    places = []
    city_data = None

    if city:
        places, city_data = search_places(
            query=query,
            city=city,
            category=category
        )

    context = {
        "query": query,
        "city": city,
        "category": category,
        "places_json": json.dumps(places),
        "city_lat": city_data["lat"] if city_data else "",
        "city_lon": city_data["lon"] if city_data else "",
    }

    return render(request, "core/search.html", context)


def index(request):
    return search_view(request)
