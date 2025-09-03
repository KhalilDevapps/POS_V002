#!/usr/bin/env python3
"""
User Management System Test Script
Tests all CRUD operations and role-based access control
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
CASHIER_CREDENTIALS = {"username": "cashier", "password": "cashier123"}

class UserManagementTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.cashier_token = None

    def login(self, credentials):
        """Login and get session with CSRF token"""
        try:
            # First get the login page to extract CSRF token
            login_page = self.session.get(f"{BASE_URL}/login")

            # Extract CSRF token from the form
            import re
            csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', login_page.text)
            csrf_token = csrf_match.group(1) if csrf_match else None

            if not csrf_token:
                print(f"❌ CSRF token not found for {credentials['username']}")
                return False

            # Add CSRF token to login data
            login_data = credentials.copy()
            login_data['csrf_token'] = csrf_token

            # Try login
            response = self.session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
            if response.status_code == 302:  # Redirect means success
                print(f"✅ Login successful for {credentials['username']}")
                return True
            else:
                print(f"❌ Login failed for {credentials['username']}: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_admin_access(self):
        """Test admin access to users page"""
        print("\n🔐 Testing Admin Access to Users Page...")

        # Login as admin
        if not self.login(ADMIN_CREDENTIALS):
            return False

        # Try to access users page
        response = self.session.get(f"{BASE_URL}/users")
        if response.status_code == 200:
            print("✅ Admin can access users page")
            return True
        else:
            print(f"❌ Admin cannot access users page: {response.status_code}")
            return False

    def test_cashier_denied_access(self):
        """Test that cashier cannot access users page"""
        print("\n🚫 Testing Cashier Access Denied...")

        # Create new session for cashier
        cashier_session = requests.Session()

        # Login as cashier
        login_response = cashier_session.post(f"{BASE_URL}/login", data=CASHIER_CREDENTIALS, allow_redirects=False)
        if login_response.status_code != 302:
            print("❌ Cashier login failed")
            return False

        # Try to access users page
        response = cashier_session.get(f"{BASE_URL}/users", allow_redirects=False)
        if response.status_code == 302:  # Should redirect
            print("✅ Cashier correctly redirected from users page")
            return True
        else:
            print(f"❌ Cashier should be denied access: {response.status_code}")
            return False

    def test_get_users_api(self):
        """Test getting users via API"""
        print("\n📋 Testing Get Users API...")

        # Login as admin
        if not self.login(ADMIN_CREDENTIALS):
            return False

        # Get users
        response = self.session.get(f"{BASE_URL}/api/users")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Retrieved {len(users)} users via API")
            for user in users:
                print(f"   - {user['username']} ({user['role']})")
            return True
        else:
            print(f"❌ Failed to get users: {response.status_code}")
            return False

    def test_add_user_api(self):
        """Test adding a new user via API"""
        print("\n➕ Testing Add User API...")

        # Login as admin
        if not self.login(ADMIN_CREDENTIALS):
            return False

        # Create test user
        test_user = {
            "username": f"testuser_{int(datetime.now().timestamp())}",
            "password": "testpass123",
            "role": "cashier"
        }

        # Add user via form (not API since we use Flask-WTF)
        response = self.session.post(f"{BASE_URL}/users", data=test_user, allow_redirects=False)

        if response.status_code == 302:  # Redirect means success
            print(f"✅ User '{test_user['username']}' added successfully")
            return test_user['username']
        else:
            print(f"❌ Failed to add user: {response.status_code}")
            return None

    def test_update_user_api(self):
        """Test updating a user via API"""
        print("\n✏️ Testing Update User API...")

        # Login as admin
        if not self.login(ADMIN_CREDENTIALS):
            return False

        # Get users first
        response = self.session.get(f"{BASE_URL}/api/users")
        if response.status_code != 200:
            print("❌ Cannot get users for update test")
            return False

        users = response.json()
        if not users:
            print("❌ No users available for update test")
            return False

        # Update the last user (avoid updating admin)
        test_user = None
        for user in reversed(users):
            if user['username'] != 'admin':
                test_user = user
                break

        if not test_user:
            print("❌ No suitable user found for update test")
            return False

        # Update user
        update_data = {
            "username": test_user['username'],
            "role": "admin" if test_user['role'] == "cashier" else "cashier"
        }

        response = self.session.put(f"{BASE_URL}/api/users/{test_user['id']}",
                                  json=update_data,
                                  headers={'Content-Type': 'application/json'})

        if response.status_code == 200:
            print(f"✅ User '{test_user['username']}' updated successfully")
            return True
        else:
            print(f"❌ Failed to update user: {response.status_code} - {response.text}")
            return False

    def test_delete_user_api(self):
        """Test deleting a user via API"""
        print("\n🗑️ Testing Delete User API...")

        # Login as admin
        if not self.login(ADMIN_CREDENTIALS):
            return False

        # Get users
        response = self.session.get(f"{BASE_URL}/api/users")
        if response.status_code != 200:
            print("❌ Cannot get users for delete test")
            return False

        users = response.json()

        # Find a test user to delete (not admin or cashier)
        test_user = None
        for user in users:
            if user['username'] not in ['admin', 'cashier']:
                test_user = user
                break

        if not test_user:
            print("❌ No test user found for deletion")
            return False

        # Delete user
        response = self.session.delete(f"{BASE_URL}/api/users/{test_user['id']}")

        if response.status_code == 200:
            print(f"✅ User '{test_user['username']}' deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete user: {response.status_code} - {response.text}")
            return False

    def run_all_tests(self):
        """Run all user management tests"""
        print("🚀 Starting User Management System Tests...")
        print("=" * 50)

        results = []

        # Test admin access
        results.append(("Admin Access", self.test_admin_access()))

        # Test cashier denied access
        results.append(("Cashier Access Denied", self.test_cashier_denied_access()))

        # Test API operations
        results.append(("Get Users API", self.test_get_users_api()))

        # Test add user
        new_user = self.test_add_user_api()
        results.append(("Add User", new_user is not None))

        # Test update user
        results.append(("Update User API", self.test_update_user_api()))

        # Test delete user (if we created one)
        if new_user:
            results.append(("Delete User API", self.test_delete_user_api()))

        # Print results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY:")
        print("=" * 50)

        passed = 0
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1

        print("=" * 50)
        print(f"🎯 Overall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All user management tests PASSED!")
            return True
        else:
            print("⚠️ Some tests failed. Check the output above.")
            return False

def main():
    """Main test function"""
    print("🧪 User Management System Test Suite")
    print("Testing Flask backend functionality...")

    # Check if Flask app is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Flask app is not running or not responding")
            print("Please start the Flask app with: python app.py")
            return
    except:
        print("❌ Cannot connect to Flask app")
        print("Please start the Flask app with: python app.py")
        return

    print("✅ Flask app is running")

    # Run tests
    tester = UserManagementTester()
    success = tester.run_all_tests()

    if success:
        print("\n🎉 User Management Backend is WORKING PERFECTLY!")
        print("The issue is likely in the frontend UI, not the backend.")
        print("\nNext steps:")
        print("1. Check browser console for JavaScript errors")
        print("2. Verify CSS files are loading")
        print("3. Check if you're logged in as admin")
        print("4. Try hard refresh (Ctrl+F5)")
    else:
        print("\n❌ User Management Backend has ISSUES!")
        print("Fix the backend issues before testing the UI.")

if __name__ == "__main__":
    main()
