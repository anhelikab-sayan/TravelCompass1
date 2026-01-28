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
    
class Route(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='routes'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"
        
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