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

### Fixed

- Corrected uuid library dependency (switched to uuid6 for better compatibility)
- Fixed broken Document.clean() validation logic
- Fixed package naming inconsistencies in setup files
- Added missing database migration file
- Improved file upload error handling

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
