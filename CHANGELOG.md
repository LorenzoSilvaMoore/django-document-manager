# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2025-08-14

### Changed

- Updated database table names with `iso_` prefix for better namespace isolation
- Optimized imports and removed unused dependencies in management commands
- Simplified Django timezone usage in City model for better consistency
- Streamlined app configuration by removing unnecessary `ready()` method

### Removed

- Deprecated `default_app_config` from package `__init__.py` (Django 3.2+ compatibility)
- Unused `os` import in `create_iso_3166` management command
- Redundant development dependencies (`pytest-cov`, `mypy`, `pre-commit`) from optional dependencies

### Fixed

- Package data configuration now correctly references `.sql` files instead of deprecated `.json` files
- Improved code maintainability with cleaner import structure

## [0.1.2] - 2025-08-13

### Added

- Version tracking with `__version__` attribute in package `__init__.py`
- Enhanced Django app configuration with proper labels and verbose names
- Explicit `app_label` in all model Meta classes for better Django integration
- Default app config declaration for improved Django compatibility

### Changed

- Updated setup.py with correct author email and GitHub repository URLs
- Improved app configuration with `ready()` method for proper model loading
- Enhanced model Meta configurations for better Django admin integration

### Removed

- Legacy test infrastructure (`runtests.py`) - cleaned up for production release

## [0.1.1] - 2025-08-11

### Added

- Comprehensive PostgreSQL dataset with 150k+ geographic records (world.sql)
- SQL-based data loading system for better performance and scalability
- Management command `create_iso_3166` to load SQL data with customizable options
- Support for custom SQL files and database targeting

### Changed

- Replaced JSON data files with SQL dump approach for better scalability
- Convert models to unmanaged with explicit db_table names
- Removed bootstrap commands in favor of direct SQL loading
- Updated MANIFEST.in to include SQL files instead of JSON files

### Removed

- JSON data files (cities.json, countries.json, regions.json, states.json, subregions.json)
- bootstrap_from_sql.py command (replaced with create_iso_3166)
- Test infrastructure and build scripts (build_and_test.py, pytest.ini, runtests.py)
- Test directory

## [0.1.0] - 2025-08-11

### Added

- Initial alpha release of django-iso-3166
- Basic geographical models and data loading functionality
- Initial models for City, Country, Region, Subregion, and State
- Django admin integration
- Complete ISO 3166 geographical data support
