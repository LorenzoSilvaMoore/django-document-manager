from django.db import models
from django.utils import timezone as tz

class City(models.Model):
    name = models.CharField(max_length=255)
    state = models.ForeignKey('State', on_delete=models.CASCADE, related_name='cities',
                             db_column='state_id')
    state_code = models.CharField(max_length=255)
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='cities',
                               db_column='country_id')
    country_code = models.CharField(max_length=2)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    timezone = models.CharField(max_length=255, blank=True, null=True,
                               help_text="IANA timezone identifier (e.g., America/New_York)")
    created_at = models.DateTimeField(default=tz.now, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    flag = models.SmallIntegerField(default=1)
    wikiDataId = models.CharField(max_length=255, blank=True, null=True,
                                 help_text="Rapid API GeoDB Cities")

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'cities'

        verbose_name = 'City'
        verbose_name_plural = 'Cities'
        indexes = [
            models.Index(fields=['state']),
            models.Index(fields=['country']),
        ]