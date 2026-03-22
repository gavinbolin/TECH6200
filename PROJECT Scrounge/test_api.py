#!/usr/bin/env python3
"""
Test script for the Scrounge API endpoints
Run this script to test all API functionality: python test_api.py
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_api_endpoints():
    """Test the API endpoints functionality"""

    # Create a session to maintain cookies
    session = requests.Session()

    print("Testing Scrounge API Endpoints")
    print("=" * 40)

    # Test 1: Unauthenticated access should return 401
    print("\n1. Testing unauthenticated access to /api/v1/inventory")
    response = session.get(f'{BASE_URL}/api/v1/inventory')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✓ Correctly returns 401 for unauthenticated access")
        data = response.json()
        print(f"Response: {data}")
    else:
        print(f"✗ Expected 401, got {response.status_code}")

    # Test 2: Unauthenticated access to specific item should return 401
    print("\n2. Testing unauthenticated access to /api/v1/inventory/test_item")
    response = session.get(f'{BASE_URL}/api/v1/inventory/test_item')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 401:
        print("✓ Correctly returns 401 for unauthenticated access")
        data = response.json()
        print(f"Response: {data}")
    else:
        print(f"✗ Expected 401, got {response.status_code}")

    # Test 3: Try to register a test user
    print("\n3. Registering a test user")
    register_data = {
        'username': 'testuser',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    response = session.post(f'{BASE_URL}/register', data=register_data)
    print(f"Registration Status: {response.status_code}")
    if response.status_code in [200, 302]:  # 302 is redirect after successful registration
        print("✓ User registration successful")
    else:
        print(f"Registration response: {response.text[:200]}...")

    # Test 4: Login with the test user
    print("\n4. Logging in with test user")
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    response = session.post(f'{BASE_URL}/login', data=login_data)
    print(f"Login Status: {response.status_code}")
    if response.status_code in [200, 302]:  # 302 is redirect after successful login
        print("✓ User login successful")
    else:
        print(f"✗ Login failed with status {response.status_code}")
        return

    # Test 5: Now test authenticated access to inventory (should be empty initially)
    print("\n5. Testing authenticated access to /api/v1/inventory")
    response = session.get(f'{BASE_URL}/api/v1/inventory')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Successfully accessed inventory API")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"✗ Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")

    # Test 6: Test accessing a non-existent item
    print("\n6. Testing access to non-existent item /api/v1/inventory/nonexistent")
    response = session.get(f'{BASE_URL}/api/v1/inventory/nonexistent')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 404:
        print("✓ Correctly returns 404 for non-existent item")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"✗ Expected 404, got {response.status_code}")
        print(f"Response: {response.text}")

    # Test 7: Add an item via the web interface and then test API
    print("\n7. Adding an item via web interface")
    add_item_data = {
        'item_name': 'test_apple',
        'quantity': '5 pieces'
    }
    response = session.post(f'{BASE_URL}/add_inventory', data=add_item_data)
    print(f"Add Item Status: {response.status_code}")

    # Test 8: Now check inventory via API again
    print("\n8. Checking inventory after adding item")
    response = session.get(f'{BASE_URL}/api/v1/inventory')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        if data.get('count', 0) > 0:
            print("✓ Inventory now contains items")
        else:
            print("✗ Inventory should contain items")
    else:
        print(f"✗ Failed to get inventory: {response.status_code}")

    # Test 9: Test accessing the specific item we just added
    print("\n9. Testing access to specific item /api/v1/inventory/test_apple")
    response = session.get(f'{BASE_URL}/api/v1/inventory/test_apple')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ Successfully accessed specific item")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"✗ Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")

    print("\n" + "=" * 40)
    print("API Testing Complete!")

if __name__ == '__main__':
    test_api_endpoints()