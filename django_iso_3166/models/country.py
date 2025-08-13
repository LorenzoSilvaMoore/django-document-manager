from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=100)
    iso3 = models.CharField(max_length=3, blank=True, null=True)
    numeric_code = models.CharField(max_length=3, blank=True, null=True)
    iso2 = models.CharField(max_length=2, blank=True, null=True)
    phonecode = models.CharField(max_length=255, blank=True, null=True)
    capital = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    currency_name = models.CharField(max_length=255, blank=True, null=True)
    currency_symbol = models.CharField(max_length=255, blank=True, null=True)
    tld = models.CharField(max_length=255, blank=True, null=True)
    native = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    region_id = models.ForeignKey('Region', on_delete=models.SET_NULL, 
                                 related_name='countries', blank=True, null=True,
                                 db_column='region_id')
    subregion = models.CharField(max_length=255, blank=True, null=True)
    subregion_id = models.ForeignKey('Subregion', on_delete=models.SET_NULL,
                                    related_name='countries', blank=True, null=True,
                                    db_column='subregion_id')
    nationality = models.CharField(max_length=255, blank=True, null=True)
    timezones = models.TextField(blank=True, null=True)
    translations = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    emoji = models.CharField(max_length=191, blank=True, null=True)
    emojiU = models.CharField(max_length=191, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    flag = models.SmallIntegerField(default=1)
    wikiDataId = models.CharField(max_length=255, blank=True, null=True,
                                 help_text="Rapid API GeoDB Cities")

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'countries'
        app_label = 'django_iso_3166'

        verbose_name = "Country"
        verbose_name_plural = "Countries"
        indexes = [
            models.Index(fields=['region_id']),
            models.Index(fields=['subregion_id']),
        ]