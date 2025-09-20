# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
 and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-09-20

### BREAKING CHANGES

- **Document Ownership System**: Migrated from string-based model identification to Django's ContentType framework
  - **Old**: `owner_model` (string) + `owner_uuid` (UUID)
  - **New**: `owner_content_type` (ContentType FK) + `owner_uuid` (UUID)
  - This change provides migration-resilient model identification that survives model renames and moves
  - Existing installations require data migration to populate `owner_content_type` from `owner_model`

### Added

- **ContentType-Based Ownership**:
  - `owner_content_type` field using Django's ContentType framework for robust model identification
  - `owner` property with intelligent caching for efficient owner instance retrieval
  - `set_owner()` method for clean owner assignment with automatic ContentType detection
  - Migration-safe architecture that survives model structure changes

- **Enhanced BaseDocumentOwnerModel**:
  - **Migration-Safe Design**: Removed callable defaults that caused Django migration issues
  - **Production-Ready**: Handles existing instances gracefully without requiring manual migrations
  - **UUID Generation**: Robust UUID7 generation with collision detection and retry logic
  - **Performance Optimization**: Built-in caching and batch processing capabilities
  - **Error Handling**: Comprehensive validation and logging for troubleshooting
  - `ensure_document_owner_uuid()` method to guarantee UUID existence for existing instances
  - Enhanced `get_documents()`, `get_documents_by_type()`, and `get_recent_documents()` methods with null UUID handling

- **Management Commands**:
  - `populate_document_owner_uuids` command for migrating existing BaseDocumentOwnerModel instances
  - Batch processing support with configurable batch sizes
  - Dry-run mode for testing migrations safely
  - Progress reporting and comprehensive error handling
  - Support for specific model targeting and verbose output

- **Advanced Document Versioning**:
  - `compute_file_hash()` method in DocumentVersion for flexible hash computation
  - Enhanced `save_new_version()` with file hash collision detection
  - Strict mode (`strict` parameter) for preventing duplicate file uploads
  - Atomic version management with database-level locking to prevent race conditions
  - Improved file integrity verification and metadata computation

### Changed

- **Document Model Architecture**:
  - **Owner Resolution**: Now uses ContentType + UUID instead of string model names
  - **Query Performance**: Optimized indexes for ContentType-based owner lookups
  - **Admin Interface**: Updated to display `owner_content_type` instead of deprecated `owner_model`
  - **API Methods**: `create_with_file()` now uses ContentType framework internally

- **BaseDocumentOwnerModel Design**:
  - **Migration Strategy**: No callable defaults to avoid "Callable default on unique field" errors
  - **Backward Compatibility**: Graceful handling of instances without UUIDs
  - **Field Configuration**: `null=True`, `blank=True` for seamless migration from existing models
  - **Index Optimization**: Uses `db_index=True` instead of separate index definitions

- **Document Validation**:
  - Enhanced validation logic to work with ContentType-based ownership
  - Improved error messages and validation feedback
  - Better separation of concerns between ownership and document metadata

### Fixed

- **Django Migration Issues**:
  - Eliminated "Callable default on unique field will not generate unique values" errors
  - Fixed migration compatibility when adding BaseDocumentOwnerModel inheritance to existing models
  - Resolved related_name conflicts in admin interface with proper `%(app_label)s_%(class)s` patterns

- **Concurrency and Performance**:
  - Fixed race conditions in document version creation with proper atomic transactions
  - Eliminated double transaction nesting in `save_new_version()`
  - Improved file hash computation efficiency and error handling
  - Enhanced query performance with ContentType-based indexes

- **Admin Interface**:
  - Fixed `owner_display()` method to use new `owner` property instead of deprecated `get_owner_instance()`
  - Updated readonly fields and fieldsets to reflect new ContentType architecture
  - Improved owner representation in admin with better fallback handling

### Technical Improvements

- **Database Design**:
  - New composite indexes: `idx_owner_ct_uuid`, `idx_document_owner_time`
  - Optimized query patterns for ContentType-based ownership lookups
  - Enhanced constraint definitions for data integrity

- **Error Handling and Logging**:
  - Comprehensive logging throughout the ownership resolution process
  - Better error messages for debugging ContentType issues
  - Improved validation error reporting in document creation workflows

- **Code Quality**:
  - Enhanced type hints throughout the codebase
  - Improved docstrings with usage examples and parameter descriptions
  - Better separation of concerns between models and their relationships

### Migration Guide

For existing installations upgrading from 0.1.x:

1. **Backup your database** before upgrading
2. **Install v0.2.0**: `pip install django-document-manager==0.2.0`
3. **Run migrations**: `python manage.py migrate django_document_manager`
4. **Populate ContentTypes**: The migration automatically populates `owner_content_type` from existing `owner_model` data
5. **Run management command**: `python manage.py populate_document_owner_uuids` to ensure all BaseDocumentOwnerModel instances have UUIDs
6. **Test ownership resolution**: Verify that `document.owner` property works correctly for your existing documents

### Deprecation Notice

- `owner_model` field is deprecated and will be removed in v0.3.0
- `get_owner_instance()` method is deprecated, use `document.owner` property instead
- Manual string-based model identification patterns should migrate to ContentType framework

This release represents a significant architectural improvement that makes the document management system more robust, migration-safe, and production-ready while maintaining backward compatibility during the transition period.

## [0.1.7] - 2025-09-15

### Fixed

- **Circular Dependency Issues**: Resolved Django migration circular dependency errors when user models and BaseDocumentOwnerModel are in the same app
  - Split initial migration into two parts: base models (0001) and user relationships (0002)
  - Created `migrate_document_manager` management command for handling circular dependencies
  - Improved `BaseDocumentOwnerModel` with runtime imports to avoid circular imports

### Added

- **Migration Management**:
  - `migrate_document_manager` command with options for skipping user dependencies
  - Automatic circular dependency detection and handling
  - Dry-run support for testing migration strategies
  - `CIRCULAR_DEPENDENCY_GUIDE.md` - Comprehensive guide for handling circular dependencies

- **Enhanced BaseDocumentOwnerModel**:
  - `get_documents_by_type()` method for filtering documents by type
  - `get_recent_documents()` method using UUID7 optimization
  - `get_owners_with_documents()` class method for finding owners with documents
  - Runtime imports to prevent circular import issues

### Changed

- **Migration Structure**: Split migrations to avoid direct AUTH_USER_MODEL dependencies in initial migration
- **Model Methods**: Enhanced BaseDocumentOwnerModel with additional utility methods and better circular import handling
- **Documentation**: Added troubleshooting section for circular dependencies in README.md

### Technical Details

This release addresses the common Django issue where circular dependency errors occur when:
1. User models and BaseDocumentOwnerModel subclasses are in the same app
2. Both depend on AUTH_USER_MODEL in their migrations
3. Django's migration system detects a circular dependency

The solution provides multiple approaches:
1. Staged migrations (recommended)
2. Separate apps for document owners (best practice)
3. Manual migration dependency management
4. Recovery strategies for existing circular dependencies

## [0.1.6] - 2025-09-15

### Fixed

- **Private Dependency Installation**: Resolved pip installation issues with private GitHub repositories
  - Removed private dependencies (`django-crud-audit`, `django-catalogs`) from automatic installation requirements
  - Created separate `requirements-private.txt` for private dependencies
  - Added comprehensive installation documentation in `INSTALL_PRIVATE_DEPS.md`
  - Updated README.md with step-by-step installation instructions for private dependencies

### Added

- **Installation Documentation**: 
  - `requirements-private.txt` - Separate requirements file for private GitHub dependencies
  - `INSTALL_PRIVATE_DEPS.md` - Comprehensive installation guide for private dependencies
  - Enhanced troubleshooting section in README.md

### Changed

- **Package Dependencies**: Private dependencies must now be installed manually before installing django-document-manager
- **Installation Process**: Two-step installation process (private deps first, then public package)

### Technical Details

This change resolves the circular dependency issue where pip fails to resolve private GitHub repositories during automatic dependency installation. Users must now:

1. Install private dependencies first with proper GitHub authentication
2. Install django-document-manager (which will install public dependencies)
3. Configure Django settings in the correct order

## [0.1.5] - 2025-09-09

### Added

- **Comprehensive Documentation**: Complete rewrite of README.md with detailed usage examples, API reference, and configuration guide
- **Missing Dependencies**: Added `django-crud-audit>=0.2.0` and `django-catalogs>=0.2.0` to package dependencies in setup.py and pyproject.toml
- **Enhanced Package Data**: Include `data/*.json` files (document type catalog data) in package distribution
- **Development Status**: Upgraded from Alpha to Beta status reflecting the maturity of the codebase

### Changed

- **Package Description**: Updated descriptions in setup.py and pyproject.toml to better reflect the comprehensive nature of the package
- **Version Consistency**: Aligned version numbers across all package files (__init__.py, setup.py, pyproject.toml)
- **Keywords Enhancement**: Added more relevant keywords including "versioning" and "validation" for better discoverability

### Documentation

- **Complete API Reference**: Detailed documentation of all models, methods, and their usage patterns
- **Advanced Examples**: Comprehensive code examples showing document creation, versioning, validation workflows, and time-based queries
- **Configuration Guide**: Complete settings reference with optional configuration options
- **Performance Notes**: Documentation of UUID7 optimization benefits and query performance characteristics
- **Database Design**: Detailed explanation of table structure, indexes, and constraints
- **Management Commands**: Full documentation of the cleanup_documents command with all options

### Technical Improvements

- **Dependency Management**: Properly declared all required dependencies for production use
- **Package Distribution**: Ensured all necessary data files are included in the package build
- **Development Workflow**: Enhanced package metadata for better development experience

### Fixed

- **Missing Dependencies**: Resolved import errors by properly declaring django-crud-audit and django-catalogs dependencies
- **Package Data**: Fixed missing document_types.json data file in package distribution

## [0.1.4] - 2025-09-04

### Added

- Comprehensive admin interface for Document, DocumentType, and DocumentVersion models
- Basic test suite for model validation and functionality
- Management command for document cleanup (`cleanup_documents`)
- uuid7-optimized database indexes for better performance
- Time-based query utilities leveraging uuid7 encoding
- Atomic transactions for version management to prevent race conditions
- Proper error handling for file operations
- Initial database migration for Document, DocumentType, and DocumentVersion models
- Management command `cleanup_documents` for automated maintenance of expired documents
  - Supports dry-run mode to preview actions before execution
  - Configurable expiration threshold (default: 30 days)
  - Option to clean up temporary upload files

### Fixed

- Corrected uuid library dependency (switched to uuid6 for better compatibility)
- Fixed broken Document.clean() validation logic
- Fixed package naming inconsistencies in setup files
- Added missing database migration file
- Improved file upload error handling
- Database table names now use 'dm_' prefix for better namespace management
  - `document` → `dm_document`
  - `document_type` → `dm_document_type`  
  - `document_version` → `dm_document_version`

### Changed

- Removed deprecated folder and tag features to keep the package lightweight
- Updated documentation to match actual implementation
- Enhanced version management with better concurrency handling
- Switched from uuid7 to uuid6 package for better ecosystem compatibility

## [0.1.3] - 2025-09-02

### Added

- First published version of the lightweight document manager
- Document, DocumentType, DocumentVersion models with uuid7 primary keys
- Flexible ownership system via BaseDocumentOwnerModel
- File versioning with automatic metadata computation
- Validation workflow with AI processing fields
- Access control levels and confidentiality flags
