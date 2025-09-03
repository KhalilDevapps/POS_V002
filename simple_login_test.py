#!/usr/bin/env python3
"""
Simple Login Test
Test login functionality directly
"""

import requests

BASE_URL = "http://127.0.0.1:5000"

def test_login():
    """Test login with different approaches"""
    print("🔐 Testing Login Functionality...")
    print("=" * 40)

    # Test 1: Check if Flask app is responding
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Flask app responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Flask app not responding: {e}")
        return

    # Test 2: Try to access login page
    try:
        response = requests.get(f"{BASE_URL}/login")
        print(f"✅ Login page accessible: {response.status_code}")
        if "login" in response.text.lower():
            print("✅ Login form found in response")
        else:
            print("⚠️ Login form not found in response")
    except Exception as e:
        print(f"❌ Cannot access login page: {e}")
        return

    # Test 3: Try login with admin credentials
    print("\n👤 Testing Admin Login...")
    session = requests.Session()

    # First get the login page to extract CSRF token
    login_page = session.get(f"{BASE_URL}/login")
    print(f"Login page status: {login_page.status_code}")

    # Extract CSRF token from the form
    import re
    csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None

    if csrf_token:
        print("✅ CSRF token extracted")
    else:
        print("❌ CSRF token not found")

    # Try login with CSRF token
    login_data = {
        "username": "admin",
        "password": "admin123",
        "csrf_token": csrf_token
    }

    login_response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    print(f"Login response status: {login_response.status_code}")

    if login_response.status_code == 302:
        print("✅ Login successful (redirect)")
        # Check where it redirects
        redirect_location = login_response.headers.get('Location', 'Unknown')
        print(f"Redirect to: {redirect_location}")

        # Try to access dashboard
        dashboard_response = session.get(f"{BASE_URL}{redirect_location}", allow_redirects=False)
        print(f"Dashboard access: {dashboard_response.status_code}")

    elif login_response.status_code == 200:
        print("⚠️ Login returned 200 (form re-display)")
        if "invalid" in login_response.text.lower() or "error" in login_response.text.lower():
            print("❌ Login failed - invalid credentials")
        else:
            print("⚠️ Login form re-displayed (possible CSRF or other issue)")
    else:
        print(f"❌ Unexpected login response: {login_response.status_code}")

    # Test 4: Try accessing users page directly (should fail without login)
    print("\n🚫 Testing Direct Users Page Access...")
    direct_response = requests.get(f"{BASE_URL}/users", allow_redirects=False)
    print(f"Direct users access: {direct_response.status_code}")

    if direct_response.status_code == 302:
        print("✅ Correctly redirected (not logged in)")
    elif direct_response.status_code == 200:
        print("❌ Should have been redirected (security issue)")
    else:
        print(f"⚠️ Unexpected response: {direct_response.status_code}")

    print("\n" + "=" * 40)
    print("🎯 Login test completed!")

if __name__ == "__main__":
    test_login()
