# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
 and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
