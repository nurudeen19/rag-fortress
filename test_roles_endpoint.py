#!/usr/bin/env python3
import requests
import json

# Try login with correct credentials
print("Testing with correct credentials...")
login_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username_or_email': 'admin',
    'password': 'admin@Rag1'
})
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data.get('token')
    print(f"✓ Got token: {token[:50]}...\n")
    
    # Test the roles endpoint with auth
    print("Testing /api/v1/admin/roles endpoint...")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('http://localhost:8000/api/v1/admin/roles', headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body:\n{response.text}\n")
    
    # Parse response
    try:
        data = response.json()
        print("Parsed JSON (formatted):")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Could not parse as JSON: {e}")
else:
    print(f"Login failed: {login_response.text}")




