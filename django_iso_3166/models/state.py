from django.db import models

class State(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='states',
                               db_column='country_id')
    country_code = models.CharField(max_length=2)
    fips_code = models.CharField(max_length=255, blank=True, null=True)
    iso2 = models.CharField(max_length=255, blank=True, null=True)
    iso3166_2 = models.CharField(max_length=10, blank=True, null=True)
    type = models.CharField(max_length=191, blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    native = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    timezone = models.CharField(max_length=255, blank=True, null=True,
                               help_text="IANA timezone identifier (e.g., America/New_York)")
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    flag = models.SmallIntegerField(default=1)
    wikiDataId = models.CharField(max_length=255, blank=True, null=True,
                                 help_text="Rapid API GeoDB Cities")

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'states'

        verbose_name = 'State'
        verbose_name_plural = 'States'
        indexes = [
            models.Index(fields=['country']),
        ]