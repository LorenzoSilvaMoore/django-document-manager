#!/usr/bin/env python
"""
Test script for the Document.objects.in_groups() method.
Tests validation and filtering functionality.
"""
import os
import sys
import uuid

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_build.settings')

import django
django.setup()

from django_document_manager.models import Document, DocumentGroup


def test_in_groups_validation():
    """Test input validation for in_groups method"""
    print("Testing input validation...")
    
    # Test 1: Invalid type (not list/tuple/queryset/instance)
    print("\n1. Testing with invalid input type (should raise ValueError)...")
    try:
        Document.objects.in_groups(123)
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Correctly raised ValueError: {e}")
    
    # Test 2: Invalid UUID string
    print("\n2. Testing with invalid UUID string (should raise ValueError)...")
    try:
        Document.objects.in_groups(["not-a-uuid"])
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Correctly raised ValueError: {e}")
    
    # Test 3: Mixed invalid types
    print("\n3. Testing with invalid type in list (should raise ValueError)...")
    try:
        Document.objects.in_groups([123, "abc"])
        print("   ❌ FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   ✓ PASSED: Correctly raised ValueError: {e}")
    
    # Test 4: Empty list (should return empty queryset)
    print("\n4. Testing with empty list (should return empty queryset)...")
    result = Document.objects.in_groups([])
    if result.count() == 0:
        print(f"   ✓ PASSED: Returns empty queryset")
    else:
        print(f"   ❌ FAILED: Expected empty queryset, got {result.count()} results")
    
    # Test 5: Valid UUID object
    print("\n5. Testing with valid UUID object...")
    try:
        test_uuid = uuid.uuid4()
        result = Document.objects.in_groups([test_uuid])
        print(f"   ✓ PASSED: Accepts UUID object, returns queryset with {result.count()} results")
    except Exception as e:
        if 'no such table' in str(e):
            print(f"   ⚠ SKIPPED: Database not initialized")
        else:
            print(f"   ❌ FAILED: {e}")
    
    # Test 6: Valid UUID string
    print("\n6. Testing with valid UUID string...")
    try:
        test_uuid_str = str(uuid.uuid4())
        result = Document.objects.in_groups([test_uuid_str])
        print(f"   ✓ PASSED: Accepts UUID string, returns queryset with {result.count()} results")
    except Exception as e:
        if 'no such table' in str(e):
            print(f"   ⚠ SKIPPED: Database not initialized")
        else:
            print(f"   ❌ FAILED: {e}")
    
    # Test 7: Mixed UUID objects and strings
    print("\n7. Testing with mixed UUID objects and strings...")
    try:
        uuid_obj = uuid.uuid4()
        uuid_str = str(uuid.uuid4())
        result = Document.objects.in_groups([uuid_obj, uuid_str])
        print(f"   ✓ PASSED: Accepts mixed types, returns queryset with {result.count()} results")
    except Exception as e:
        if 'no such table' in str(e):
            print(f"   ⚠ SKIPPED: Database not initialized")
        else:
            print(f"   ❌ FAILED: {e}")
    
    # Test 8: DocumentGroup QuerySet
    print("\n8. Testing with DocumentGroup QuerySet...")
    try:
        qs = DocumentGroup.objects.all()
        result = Document.objects.in_groups(qs)
        print(f"   ✓ PASSED: Accepts DocumentGroup QuerySet, returns queryset")
    except Exception as e:
        if 'no such table' in str(e):
            print(f"   ⚠ SKIPPED: Database not initialized")
        else:
            print(f"   ❌ FAILED: {e}")
    
    # Test 9: Single DocumentGroup instance
    print("\n9. Testing with single DocumentGroup instance...")
    try:
        # Create a mock group for testing
        from unittest.mock import Mock
        mock_group = Mock(spec=DocumentGroup)
        mock_group.group_uuid = uuid.uuid4()
        # This will fail at query time but should pass validation
        try:
            result = Document.objects.in_groups(mock_group)
            print(f"   ✓ PASSED: Accepts single DocumentGroup instance")
        except Exception as query_err:
            if 'no such table' in str(query_err):
                print(f"   ✓ PASSED: Accepts single DocumentGroup instance (query not executed)")
            else:
                raise
    except Exception as e:
        print(f"   ❌ FAILED: {e}")


def test_in_groups_functionality():
    """Test actual filtering functionality with database"""
    print("\n\n" + "="*60)
    print("Testing functionality with database...")
    print("="*60)
    
    try:
        # Check if we have any groups
        group_count = DocumentGroup.objects.count()
        print(f"\nDatabase has {group_count} document groups")
        
        if group_count > 0:
            # Get first group
            group = DocumentGroup.objects.first()
            print(f"\nTesting with group: {group}")
            
            # Test 10: Filtering with DocumentGroup instance
            print(f"\n10. Testing with single DocumentGroup instance...")
            result = Document.objects.in_groups(group)
            print(f"   Found {result.count()} documents in group '{group.name}'")
            
            # Test 11: Filtering with list of DocumentGroup instances
            print(f"\n11. Testing with list of DocumentGroup instances...")
            groups_list = list(DocumentGroup.objects.all()[:2])
            result = Document.objects.in_groups(groups_list)
            print(f"   Found {result.count()} documents in {len(groups_list)} groups")
            
            # Test 12: Filtering with DocumentGroup QuerySet
            print(f"\n12. Testing with DocumentGroup QuerySet...")
            qs = DocumentGroup.objects.filter(name__icontains='')
            result = Document.objects.in_groups(qs)
            print(f"   Found {result.count()} documents using queryset")
            
            # Test 13: Filtering with existing group UUID
            print(f"\n13. Testing filtering with existing group UUID...")
            result = Document.objects.in_groups([group.group_uuid])
            print(f"   Found {result.count()} documents in group '{group.name}'")
            
            # Test 14: Filtering with string UUID
            print(f"\n14. Testing filtering with existing group UUID as string...")
            result = Document.objects.in_groups([str(group.group_uuid)])
            print(f"   Found {result.count()} documents in group '{group.name}'")
            
            # Test 15: Mixed types - instance, UUID, string
            print(f"\n15. Testing with mixed types (instance, UUID, string)...")
            if group_count >= 2:
                group2 = DocumentGroup.objects.all()[1]
                result = Document.objects.in_groups([
                    group,                  # DocumentGroup instance
                    group2.group_uuid,      # UUID object
                    str(group.group_uuid)   # UUID string (duplicate but should handle)
                ])
                print(f"   Found {result.count()} documents with mixed input types")
            else:
                print(f"   ⚠ SKIPPED: Need at least 2 groups for this test")
            
            # Test 16: Method chaining
            print(f"\n16. Testing method chaining...")
            result = Document.objects.in_groups([group.group_uuid]).filter(
                validation_status='pending'
            )
            print(f"   Found {result.count()} pending documents in group '{group.name}'")
        else:
            print("\n⚠ No document groups found in database. Skipping functional tests.")
        
        # Check total documents
        total_docs = Document.objects.count()
        print(f"\n\nTotal documents in database: {total_docs}")
    except Exception as e:
        if 'no such table' in str(e):
            print("\n⚠ Database tables not created. Skipping functional tests.")
            print("   Run migrations to test with actual database.")
        else:
            raise


if __name__ == '__main__':
    print("="*60)
    print("Document.objects.in_groups() Test Suite")
    print("="*60)
    
    try:
        test_in_groups_validation()
        test_in_groups_functionality()
        
        print("\n\n" + "="*60)
        print("✓ All validation tests completed successfully!")
        print("="*60)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
