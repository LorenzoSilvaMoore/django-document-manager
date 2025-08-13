from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100)
    translations = models.TextField(blank=True, null=True)  # Changed from JSONField to TextField to match SQL
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    flag = models.SmallIntegerField(default=1)
    wikiDataId = models.CharField(max_length=255, blank=True, null=True, 
                                 help_text="Rapid API GeoDB Cities")

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'regions'
        app_label = 'django_iso_3166'

        verbose_name = "Region"
        verbose_name_plural = "Regions"