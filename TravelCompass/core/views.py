import json

from django.shortcuts import render
from django.utils.safestring import mark_safe

from core.api.d2gis import search_places


def main_view(request):
    places = []
    query = request.GET.get("q")

    if query:
        places = search_places(query)

    return render(request, "main.html", {
        "places": places,
        "places_json": mark_safe(json.dumps(places)),
        "query": query,
    })
