# filepath: django-iso-3166/README.md

# Django ISO 3166

Django ISO 3166 is a Django application that provides models for managing geographical data, including cities, countries, regions, subregions, and states. This package allows for easy integration and management of geographical information in Django projects.

## Features

- Models for cities, countries, regions, subregions, and states.
- Custom management command to bootstrap the database with initial data.
- Easy integration with Django's admin interface for data management.

## Installation

To install Django ISO 3166, you can use pip:

```bash
pip install django-iso-3166
```

## Usage

1. **Add to Installed Apps**: Add `django_iso_3166` to your `INSTALLED_APPS` in your Django settings.

   ```python
   INSTALLED_APPS = [
       ...
       'django_iso_3166',
   ]
   ```

2. **Run Migrations**: Apply the migrations to create the necessary database tables.

   ```bash
   python manage.py migrate
   ```

3. **Bootstrap the Database**: Use the custom management command to populate the database with initial data.

   ```bash
   python manage.py bootstrap_geo
   ```

## Models

The following models are included in this package:

- **City**: Represents a city with fields for name, state, country, latitude, longitude, and timezone.
- **Country**: Represents a country with fields for name, ISO codes, capital, currency, region, and subregion.
- **Region**: Represents a geographical region with fields for name and translations.
- **Subregion**: Represents a subregion with fields for name and translations.
- **State**: Represents a state with fields for name, country, and ISO code.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Changelog

See the [CHANGELOG.md](CHANGELOG.md) for a list of changes and updates to the project.