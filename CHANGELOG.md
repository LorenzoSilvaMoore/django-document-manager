# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
 and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
