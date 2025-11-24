#!/bin/bash
# Test runner for django-document-manager
# Runs all tests sequentially with clear output

echo "=========================================="
echo "Django Document Manager - Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "Running migrations..."
python manage.py migrate --noinput > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Migrations applied"
echo ""

echo "=========================================="
echo "Test Suite: v0.2.7 Features"
echo "=========================================="
echo ""

# Run v0.2.7 tests
if python manage.py test test_app.tests.test_v0_2_7 --verbosity=1; then
    echo -e "${GREEN}✓ v0.2.7 tests PASSED${NC}"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗ v0.2.7 tests FAILED${NC}"
    ((FAILED_TESTS++))
fi
echo ""

echo "=========================================="
echo "Test Suite: Core Functionality"
echo "=========================================="
echo ""

# Run core functionality tests with PYTHONPATH set
if PYTHONPATH=. python test_app/tests/test_core_functionality.py; then
    echo -e "${GREEN}✓ Core functionality tests PASSED${NC}"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗ Core functionality tests FAILED${NC}"
    ((FAILED_TESTS++))
fi
echo ""

echo "=========================================="
echo "Test Suite: Document Groups"
echo "=========================================="
echo ""

# Run in_groups tests with PYTHONPATH set
if PYTHONPATH=. python test_app/tests/test_in_groups.py; then
    echo -e "${GREEN}✓ Document groups tests PASSED${NC}"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗ Document groups tests FAILED${NC}"
    ((FAILED_TESTS++))
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))
echo "Total test suites run: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
