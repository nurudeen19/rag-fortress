#!/usr/bin/env python3
import requests
import json

# Login first
login_response = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username_or_email': 'admin',
    'password': 'admin@Rag1'
})

if login_response.status_code == 200:
    login_data = login_response.json()
    token = login_data.get('token')
    print(f"✓ Got token\n")
    
    # Test the users endpoint
    print("Testing /api/v1/admin/users endpoint...")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('http://localhost:8000/api/v1/admin/users?limit=50&offset=0&active_only=true', headers=headers)
    print(f"Status Code: {response.status_code}")
    
    # Parse response
    try:
        data = response.json()
        print("Users:")
        if 'users' in data:
            for user in data['users']:
                print(f"  - {user['username']} ({user['email']})")
            print(f"\nTotal users: {data.get('total', 'N/A')}")
        else:
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {response.text}")
else:
    print(f"Login failed")
