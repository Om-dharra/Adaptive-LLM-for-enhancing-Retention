
import requests
import json

url = "http://127.0.0.1:8000/auth/"
headers = {"Content-Type": "application/json"}
import random
import string

rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
data = {
    "username": f"om_{rand_suffix}",
    "password": "test",
    "email": f"test_{rand_suffix}@gmail.com"
}

try:
    # 1. Create a specific user to ensure it exists
    duplicate_user = "duplicate_test_user"
    data["username"] = duplicate_user
    data["email"] = "duplicate@test.com"

    print(f"Creating user first time: {duplicate_user}")
    response = requests.post(url, headers=headers, json=data)
    print(f"First Create Status: {response.status_code}")

    # 2. Create SAME user again
    print(f"Creating user second time (should be 400 but might be 500): {duplicate_user}")
    response = requests.post(url, headers=headers, json=data)
    print(f"Second Create Status: {response.status_code}")
    print(f"Second Create Response: {response.text}")


    # 2. Login User (this should fail/crash)
    print("Attempting login...")
    token_url = "http://127.0.0.1:8000/auth/token"
    login_data = {
        "grant_type": "",
        "username": data["username"],
        "password": data["password"],
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    # Using data= for form-encoded
    login_response = requests.post(token_url, data=login_data)
    print(f"Login Status: {login_response.status_code}")
    print(f"Login Response: {login_response.text}")

except Exception as e:
    print(f"Request failed: {e}")
