from django.db import models
from django.contrib.auth.models import User


class Place(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    dg2is_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID объекта из 2ГИС"
    )

    def __str__(self):
        return self.name

# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Route(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200, blank=True, default='')
    
    # ВАЖНО: У всех полей должны быть default значения!
    start_point_lat = models.FloatField(default=0.0)
    start_point_lon = models.FloatField(default=0.0)
    start_point_address = models.CharField(max_length=500, blank=True, default='')
    
    end_point_lat = models.FloatField(default=0.0)
    end_point_lon = models.FloatField(default=0.0)
    end_point_address = models.CharField(max_length=500, blank=True, default='')
    
    end_type = models.CharField(max_length=50, default='start')
    total_distance = models.FloatField(default=0.0)
    total_duration = models.FloatField(default=0.0)  # Вот здесь важно!
    walking_time = models.IntegerField(default=60)
    city_name = models.CharField(max_length=100, blank=True, default='')
    
    categories = models.JSONField(default=list)
    route_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title or 'Маршрут'} - {self.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    @property
    def formatted_distance(self):
        if self.total_distance < 1000:
            return f"{self.total_distance:.0f} м"
        return f"{self.total_distance/1000:.1f} км"
    
    @property
    def formatted_duration(self):
        minutes = int(self.total_duration / 60)
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours} ч {mins} мин"
        return f"{mins} мин"
        
class RoutePoint(models.Model):

    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='points'
    )
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='route_points'
    )
    order = models.PositiveIntegerField(
        help_text="Порядок точки в маршруте"
    )

    class Meta:
        ordering = ['order']
        unique_together = ('route', 'order')

    def __str__(self):
        return f"{self.route.title} - {self.place.name} ({self.order})"