#!/usr/bin/env python3
"""
API Testing Example
Demonstrates automated API testing capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_automation_framework.tools.scheduler_and_testing import APITestingTool


def demo_api_testing():
    """Demonstrate API testing capabilities."""
    print("=" * 60)
    print("API TESTING DEMO")
    print("=" * 60)

    tester = APITestingTool()

    print("\n1. TESTING SINGLE ENDPOINT")
    print("-" * 60)

    # Test a public API
    try:
        result = tester.test_endpoint(
            url="https://jsonplaceholder.typicode.com/posts/1",
            method="GET",
            expected_status=200
        )

        print(f"✓ Test URL: {result['url']}")
        print(f"✓ Method: {result['method']}")
        print(f"✓ Status Code: {result['status_code']} (Expected: {result['expected_status']})")
        print(f"✓ Response Time: {result['response_time']}s")
        print(f"✓ Test Passed: {result['success']}")
        print(f"\nResponse Preview:")
        print(f"  {str(result['response'])[:200]}...")
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        print("Continuing with demo...")

    print("\n2. TESTING MULTIPLE ENDPOINTS")
    print("-" * 60)

    endpoints = [
        {
            "url": "https://jsonplaceholder.typicode.com/posts/1",
            "method": "GET",
            "expected_status": 200
        },
        {
            "url": "https://jsonplaceholder.typicode.com/users/1",
            "method": "GET",
            "expected_status": 200
        },
        {
            "url": "https://jsonplaceholder.typicode.com/comments",
            "method": "GET",
            "expected_status": 200
        },
    ]

    try:
        results = tester.test_multiple_endpoints(endpoints)

        print(f"✓ Total Tests: {results['total_tests']}")
        print(f"✓ Passed: {results['passed']}")
        print(f"✓ Failed: {results['failed']}")
        print(f"✓ Pass Rate: {results['pass_rate']}%")

        print("\nDetailed Results:")
        for i, test in enumerate(results['results'], 1):
            status = "✓ PASS" if test['success'] else "✗ FAIL"
            print(f"  {i}. {test['url']} - {status} ({test['response_time']}s)")
    except Exception as e:
        print(f"Error testing multiple endpoints: {e}")
        print("Continuing with demo...")

    print("\n3. LOAD TESTING")
    print("-" * 60)
    print("Running load test with 50 requests...")

    try:
        load_result = tester.load_test(
            url="https://jsonplaceholder.typicode.com/posts/1",
            method="GET",
            num_requests=50,
            concurrent=False  # Sequential for demo
        )

        print(f"\n✓ Total Requests: {load_result['total_requests']}")
        print(f"✓ Successful: {load_result['total_requests'] - load_result['errors']}")
        print(f"✓ Errors: {load_result['errors']}")
        print(f"✓ Success Rate: {load_result['success_rate']}%")
        print(f"✓ Total Time: {load_result['total_time']}s")
        print(f"✓ Avg Response Time: {load_result['avg_response_time']}s")
        print(f"✓ Min Response Time: {load_result['min_response_time']}s")
        print(f"✓ Max Response Time: {load_result['max_response_time']}s")
        print(f"✓ Requests/Second: {load_result['requests_per_second']}")
    except Exception as e:
        print(f"Error during load testing: {e}")
        print("Continuing with demo...")

    print("\n4. RESPONSE SCHEMA VALIDATION")
    print("-" * 60)

    # Sample API response
    api_response = {
        "id": 1,
        "title": "Test Post",
        "body": "This is a test post",
        "userId": 1
    }

    # Expected schema
    expected_schema = {
        "id": int,
        "title": str,
        "body": str,
        "userId": int
    }

    validation = tester.validate_response_schema(api_response, expected_schema)

    print(f"✓ Valid: {validation['valid']}")
    print(f"✓ Checked Fields: {validation['checked_fields']}")
    if validation['errors']:
        print(f"✗ Errors: {validation['errors']}")
    else:
        print(f"✓ No validation errors")

    # Test with invalid schema
    print("\nTesting invalid schema:")
    invalid_response = {"id": "wrong_type", "title": 123}

    validation = tester.validate_response_schema(invalid_response, expected_schema)
    print(f"✓ Valid: {validation['valid']}")
    print(f"✗ Errors found:")
    for error in validation['errors']:
        print(f"    • {error}")

    print("\n5. COMPREHENSIVE TEST REPORT")
    print("-" * 60)

    report = tester.get_test_report()

    print(f"\n📊 Test Summary Report:")
    print(f"  • Total Tests Run: {report['total_tests']}")
    print(f"  • Passed: {report['passed']}")
    print(f"  • Failed: {report['failed']}")
    print(f"  • Pass Rate: {report['pass_rate']}%")
    print(f"  • Average Response Time: {report['avg_response_time']}s")

    print("\n6. PRACTICAL USE CASES")
    print("-" * 60)

    use_cases = """
Use Case 1: CI/CD Pipeline Testing
  • Run API tests before deployment
  • Validate all endpoints
  • Check response times
  • Fail build if tests fail

Use Case 2: API Monitoring
  • Schedule hourly health checks
  • Monitor response times
  • Alert on failures
  • Track API performance

Use Case 3: Load Testing
  • Test API under load
  • Find performance bottlenecks
  • Determine rate limits
  • Optimize infrastructure

Use Case 4: Contract Testing
  • Validate API responses
  • Ensure schema compliance
  • Catch breaking changes
  • Maintain API consistency
"""
    print(use_cases)


def example_test_suite():
    """Show example test suite."""
    print("\n" + "=" * 60)
    print("EXAMPLE TEST SUITE")
    print("=" * 60)

    code = '''
# Comprehensive API test suite
from api_testing_tool import APITestingTool

tester = APITestingTool()

# Define test cases
test_cases = [
    # User endpoints
    {
        "url": "https://api.example.com/users",
        "method": "GET",
        "expected_status": 200,
        "name": "List all users"
    },
    {
        "url": "https://api.example.com/users/1",
        "method": "GET",
        "expected_status": 200,
        "name": "Get specific user"
    },

    # Post endpoints
    {
        "url": "https://api.example.com/posts",
        "method": "POST",
        "data": {"title": "Test", "body": "Test content"},
        "expected_status": 201,
        "name": "Create post"
    },

    # Error handling
    {
        "url": "https://api.example.com/users/99999",
        "method": "GET",
        "expected_status": 404,
        "name": "Non-existent resource"
    },
]

# Run tests
results = tester.test_multiple_endpoints(test_cases)

# Generate report
report = tester.get_test_report()

# Assert pass rate
assert report['pass_rate'] >= 95, "Tests failed: Pass rate below 95%"

print(f"✓ All tests completed: {report['pass_rate']}% pass rate")
'''

    print(code)


if __name__ == "__main__":
    demo_api_testing()
    example_test_suite()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ Single endpoint testing")
    print("  ✓ Multiple endpoint testing")
    print("  ✓ Load testing")
    print("  ✓ Schema validation")
    print("  ✓ Performance metrics")
    print("  ✓ Comprehensive reporting")
