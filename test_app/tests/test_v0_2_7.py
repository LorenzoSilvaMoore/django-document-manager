"""
Test cases for django-document-manager v0.2.7 features

Tests for:
1. File validation with error codes (invalid_extension, file_too_large)
2. max_count_per_owner constraint on DocumentType
3. Validation timing fixes
"""

from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

from django_document_manager.models import (
    Document, DocumentType, DocumentVersion
)
from test_app.models import TestCompany, TestPerson


class FileValidationErrorCodesTestCase(TestCase):
    """Test error codes for file validation"""
    
    def setUp(self):
        """Create test owner and document types"""
        self.owner = TestCompany.objects.create(name='Test Company')
        
        self.pdf_only_type = DocumentType.objects.create(
            code='test_pdf_only',
            name='PDF Only Type',
            file_extensions=['.pdf'],
            max_file_size_mb=10
        )
        
        self.small_file_type = DocumentType.objects.create(
            code='test_small',
            name='Small File Type',
            file_extensions=['.pdf', '.txt'],
            max_file_size_mb=5
        )
        
    def create_test_file(self, filename, size_mb=1):
        """Create a test file with specified size"""
        content = b'X' * int(size_mb * 1024 * 1024)
        return ContentFile(content, name=filename)
        
    def test_invalid_extension_error_code(self):
        """Test that invalid file extension raises error with code 'invalid_extension'"""
        docx_file = self.create_test_file('test.docx', size_mb=0.5)
        
        with self.assertRaises(ValidationError) as cm:
            Document.create_with_file(
                owner=self.owner,
                file=docx_file,
                document_type=self.pdf_only_type,
                title='Invalid Extension Test'
            )
        
        # Check that error has the correct code
        error = cm.exception
        self.assertIn('file', error.error_dict)
        
        file_errors = error.error_dict['file']
        error_codes = [err.code for err in file_errors if hasattr(err, 'code')]
        self.assertIn('invalid_extension', error_codes)
        
    def test_file_too_large_error_code(self):
        """Test that oversized file raises error with code 'file_too_large'"""
        large_file = self.create_test_file('large.pdf', size_mb=10)
        
        with self.assertRaises(ValidationError) as cm:
            Document.create_with_file(
                owner=self.owner,
                file=large_file,
                document_type=self.small_file_type,
                title='Large File Test'
            )
        
        # Check that error has the correct code
        error = cm.exception
        self.assertIn('file', error.error_dict)
        
        file_errors = error.error_dict['file']
        error_codes = [err.code for err in file_errors if hasattr(err, 'code')]
        self.assertIn('file_too_large', error_codes)
        
    def test_error_code_distinction(self):
        """Test that we can distinguish between extension and size errors"""
        doc_type = DocumentType.objects.create(
            code='test_restricted',
            name='Restricted Type',
            file_extensions=['.pdf'],
            max_file_size_mb=2
        )
        
        # Test extension error
        wrong_ext_file = self.create_test_file('test.txt', size_mb=1)
        
        with self.assertRaises(ValidationError) as cm:
            Document.create_with_file(
                owner=self.owner,
                file=wrong_ext_file,
                document_type=doc_type,
                title='Extension Error Test'
            )
        
        error = cm.exception
        if 'file' in error.error_dict:
            error_codes = [err.code for err in error.error_dict['file'] if hasattr(err, 'code')]
            self.assertIn('invalid_extension', error_codes)
        
        # Test size error
        oversized_file = self.create_test_file('test.pdf', size_mb=5)
        
        with self.assertRaises(ValidationError) as cm:
            Document.create_with_file(
                owner=self.owner,
                file=oversized_file,
                document_type=doc_type,
                title='Size Error Test'
            )
        
        error = cm.exception
        if 'file' in error.error_dict:
            error_codes = [err.code for err in error.error_dict['file'] if hasattr(err, 'code')]
            self.assertIn('file_too_large', error_codes)


class MaxCountPerOwnerTestCase(TestCase):
    """Test max_count_per_owner constraint"""
    
    def setUp(self):
        """Create test owners"""
        self.owner1 = TestCompany.objects.create(name='Company 1')
        self.owner2 = TestCompany.objects.create(name='Company 2')
        
    def create_test_file(self, filename, size_mb=1):
        """Create a test file"""
        content = b'X' * int(size_mb * 1024 * 1024)
        return ContentFile(content, name=filename)
        
    def test_unlimited_documents(self):
        """Test that max_count_per_owner=0 allows unlimited documents"""
        doc_type = DocumentType.objects.create(
            code='test_unlimited',
            name='Unlimited Type',
            file_extensions=['.pdf'],
            max_file_size_mb=10,
            max_count_per_owner=0  # Unlimited
        )
        
        # Create 5 documents
        for i in range(5):
            test_file = self.create_test_file(f'test_{i}.pdf', size_mb=1)
            Document.create_with_file(
                owner=self.owner1,
                file=test_file,
                document_type=doc_type,
                title=f'Unlimited Test {i}'
            )
        
        # Verify all were created
        doc_count = Document.objects.filter(
            owner_uuid=self.owner1.document_owner_uuid,
            document_type=doc_type
        ).count()
        
        self.assertEqual(doc_count, 5)
        
    def test_limit_enforced(self):
        """Test that max_count_per_owner limit is enforced"""
        doc_type = DocumentType.objects.create(
            code='test_limited',
            name='Limited Type',
            file_extensions=['.pdf'],
            max_file_size_mb=10,
            max_count_per_owner=3  # Max 3 per owner
        )
        
        # Create 3 documents (should succeed)
        for i in range(3):
            test_file = self.create_test_file(f'test_{i}.pdf', size_mb=1)
            Document.create_with_file(
                owner=self.owner1,
                file=test_file,
                document_type=doc_type,
                title=f'Limited Test {i}'
            )
        
        # Try to create 4th document (should fail)
        test_file = self.create_test_file('test_4.pdf', size_mb=1)
        
        with self.assertRaises(ValidationError) as cm:
            Document.create_with_file(
                owner=self.owner1,
                file=test_file,
                document_type=doc_type,
                title='Limited Test 4 (Should Fail)'
            )
        
        # Check for the correct error code
        error = cm.exception
        self.assertEqual(error.code, 'max_count_exceeded')
        
    def test_limit_per_owner(self):
        """Test that max_count_per_owner is enforced per owner"""
        doc_type = DocumentType.objects.create(
            code='test_per_owner',
            name='Per Owner Type',
            file_extensions=['.pdf'],
            max_file_size_mb=10,
            max_count_per_owner=2
        )
        
        # Owner 1: Create 2 documents
        for i in range(2):
            test_file = self.create_test_file(f'owner1_test_{i}.pdf', size_mb=1)
            Document.create_with_file(
                owner=self.owner1,
                file=test_file,
                document_type=doc_type,
                title=f'Owner1 Test {i}'
            )
        
        # Owner 2: Should still be able to create 2 documents
        for i in range(2):
            test_file = self.create_test_file(f'owner2_test_{i}.pdf', size_mb=1)
            Document.create_with_file(
                owner=self.owner2,
                file=test_file,
                document_type=doc_type,
                title=f'Owner2 Test {i}'
            )
        
        # Verify counts
        owner1_count = Document.objects.filter(
            owner_uuid=self.owner1.document_owner_uuid,
            document_type=doc_type
        ).count()
        owner2_count = Document.objects.filter(
            owner_uuid=self.owner2.document_owner_uuid,
            document_type=doc_type
        ).count()
        
        self.assertEqual(owner1_count, 2)
        self.assertEqual(owner2_count, 2)


class ValidationTimingTestCase(TestCase):
    """Test that validation happens at the correct time"""
    
    def setUp(self):
        """Create test owner and document type"""
        self.owner = TestCompany.objects.create(name='Timing Test Company')
        self.doc_type = DocumentType.objects.create(
            code='test_timing',
            name='Timing Test Type',
            file_extensions=['.pdf'],
            max_file_size_mb=10
        )
        
    def create_test_file(self, filename, size_mb=1):
        """Create a test file"""
        content = b'X' * int(size_mb * 1024 * 1024)
        return ContentFile(content, name=filename)
        
    def test_metadata_computed_before_validation(self):
        """Test that validation happens after metadata computation"""
        test_file = self.create_test_file('test.pdf', size_mb=2)
        
        # This should work without errors about null fields
        document = Document.create_with_file(
            owner=self.owner,
            file=test_file,
            document_type=self.doc_type,
            title='Timing Test'
        )
        
        # Verify that metadata was computed
        version = document.get_current_version()
        self.assertIsNotNone(version)
        self.assertIsNotNone(version.file_size_bytes)
        self.assertIsNotNone(version.file_hash)
        self.assertIsNotNone(version.mime_type)
        self.assertIsNotNone(version.version)
        self.assertGreater(version.version, 0)
        
    def test_valid_files_pass_validation(self):
        """Test that valid files pass all validations"""
        doc_type = DocumentType.objects.create(
            code='test_valid',
            name='Valid File Type',
            file_extensions=['.pdf', '.docx', '.txt'],
            max_file_size_mb=10,
            max_count_per_owner=5
        )
        
        # Test different valid file types
        test_files = [
            ('document.pdf', 2),
            ('report.docx', 3),
            ('notes.txt', 1),
        ]
        
        for filename, size_mb in test_files:
            test_file = self.create_test_file(filename, size_mb=size_mb)
            document = Document.create_with_file(
                owner=self.owner,
                file=test_file,
                document_type=doc_type,
                title=f'Valid {filename}'
            )
            self.assertIsNotNone(document.pk)
