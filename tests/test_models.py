from django.test import TestCase
from django_iso_3166.models import Country, Region, Subregion, State, City

class ModelsTestCase(TestCase):
    def setUp(self):
        self.region = Region.objects.create(
            id=1,
            name="Test Region",
            translations={"es": "Región de Prueba"}
        )
        
        self.subregion = Subregion.objects.create(
            id=1,
            name="Test Subregion",
            translations={"es": "Subregión de Prueba"}
        )
        
        self.country = Country.objects.create(
            id=1,
            name="Test Country",
            iso2="TC",
            iso3="TCY",
            numeric_code="999",
            capital="Test Capital",
            currency="Test Currency",
            region=self.region,
            subregion=self.subregion
        )
        
        self.state = State.objects.create(
            id=1,
            name="Test State",
            country=self.country,
            iso2="TS"
        )
        
        self.city = City.objects.create(
            id=1,
            name="Test City",
            state=self.state,
            country=self.country,
            latitude="40.7128",
            longitude="-74.0060",
            timezone="America/New_York"
        )

    def test_country_creation(self):
        self.assertEqual(self.country.name, "Test Country")
        self.assertEqual(self.country.iso2, "TC")
        self.assertEqual(str(self.country), "Test Country")

    def test_region_creation(self):
        self.assertEqual(self.region.name, "Test Region")
        self.assertEqual(str(self.region), "Test Region")

    def test_state_creation(self):
        self.assertEqual(self.state.name, "Test State")
        self.assertEqual(self.state.country, self.country)
        self.assertEqual(str(self.state), "Test State")

    def test_city_creation(self):
        self.assertEqual(self.city.name, "Test City")
        self.assertEqual(self.city.state, self.state)
        self.assertEqual(self.city.country, self.country)
        self.assertEqual(str(self.city), "Test City")
