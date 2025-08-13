from django.db import models

class Subregion(models.Model):
    name = models.CharField(max_length=100)
    translations = models.TextField(blank=True, null=True)  # Changed from JSONField to TextField
    region = models.ForeignKey('Region', on_delete=models.CASCADE, related_name='subregions')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    flag = models.SmallIntegerField(default=1)
    wikiDataId = models.CharField(max_length=255, blank=True, null=True,
                                 help_text="Rapid API GeoDB Cities")

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'subregions'
        app_label = 'django_iso_3166'

        verbose_name = "Subregion"
        verbose_name_plural = "Subregions"