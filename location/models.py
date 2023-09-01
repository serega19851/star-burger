from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(
            'адрес',
            max_length=100,
            db_index=True,
            unique=True
            )
    query_date = models.DateField(
            'дата запроса',
            db_index=True,
            default=timezone.now
            )
    lat = models.FloatField('широта', null=True, blank=True)
    lon = models.FloatField('долгота', null=True, blank=True)

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'

    def __str__(self):
        return f'{self.address} - ({self.lat}, {self.lon})'
