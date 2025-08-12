from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
import json
import os
from pathlib import Path
from django_iso_3166.models import City, Country, Region, Subregion, State

class Command(BaseCommand):
    help = 'Bootstrap the geographic data into the database'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get the path to the data directory relative to this file
        current_dir = Path(__file__).parent.parent.parent
        self.data_dir = current_dir / 'data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to bootstrap geographic data...'))

        self.load_regions()
        self.load_subregions()
        self.load_countries()
        self.load_states()
        self.load_cities()

        self.stdout.write(self.style.SUCCESS('Geographic data bootstrapped successfully!'))

    def load_regions(self):
        with open(self.data_dir / 'regions.json', 'r', encoding='utf-8') as f:
            regions = json.load(f)
            for region_data in regions:
                Region.objects.update_or_create(
                    id=region_data['id'],
                    defaults={'name': region_data['name'], 'translations': region_data.get('translations', {})}
                )

    def load_subregions(self):
        with open(self.data_dir / 'subregions.json', 'r', encoding='utf-8') as f:
            subregions = json.load(f)
            for subregion_data in subregions:
                Subregion.objects.update_or_create(
                    id=subregion_data['id'],
                    defaults={'name': subregion_data['name'], 'translations': subregion_data.get('translations', {})}
                )

    def load_countries(self):
        with open(self.data_dir / 'countries.json', 'r', encoding='utf-8') as f:
            countries = json.load(f)
            for country_data in countries:
                region = self.get_region(country_data.get('region_id'))
                subregion = self.get_subregion(country_data.get('subregion_id'))
                Country.objects.update_or_create(
                    id=country_data['id'],
                    defaults={
                        'name': country_data['name'],
                        'iso2': country_data['iso2'],
                        'iso3': country_data['iso3'],
                        'numeric_code': country_data['numeric_code'],
                        'capital': country_data['capital'],
                        'currency': country_data['currency'],
                        'region': region,
                        'subregion': subregion
                    }
                )

    def load_states(self):
        with open(self.data_dir / 'states.json', 'r', encoding='utf-8') as f:
            states = json.load(f)
            for state_data in states:
                country = self.get_country(state_data.get('country_id'))
                State.objects.update_or_create(
                    id=state_data['id'],
                    defaults={'name': state_data['name'], 'country': country, 'iso2': state_data.get('iso2')}
                )

    def load_cities(self):
        with open(self.data_dir / 'cities.json', 'r', encoding='utf-8') as f:
            cities = json.load(f)
            for city_data in cities:
                state = self.get_state(city_data.get('state_id'))
                country = self.get_country(city_data.get('country_id'))
                City.objects.update_or_create(
                    id=city_data['id'],
                    defaults={
                        'name': city_data['name'],
                        'state': state,
                        'country': country,
                        'latitude': city_data['latitude'],
                        'longitude': city_data['longitude'],
                        'timezone': city_data.get('timezone')
                    }
                )

    def get_region(self, region_id):
        try:
            return Region.objects.get(id=region_id)
        except ObjectDoesNotExist:
            return None

    def get_subregion(self, subregion_id):
        try:
            return Subregion.objects.get(id=subregion_id)
        except ObjectDoesNotExist:
            return None

    def get_country(self, country_id):
        try:
            return Country.objects.get(id=country_id)
        except ObjectDoesNotExist:
            return None

    def get_state(self, state_id):
        try:
            return State.objects.get(id=state_id)
        except ObjectDoesNotExist:
            return None