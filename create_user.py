import requests

# Replace with your server URL
BASE_URL = "http://127.0.0.1:8000"

def create_user(username, password):
    url = f"{BASE_URL}/create_user"
    payload = {
        "username": username,
        "password": password
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ User created successfully!")
        print(f"🔑 API Key: {data['api_key']}")
    else:
        print(f"❌ Failed to create user: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    # Replace these with desired credentials
    username = "john"
    password = "secret12356"

    create_user(username, password)
