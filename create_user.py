import requests

# Replace with your server URL
BASE_URL = "http://127.0.0.1:8000"

output_file = "user_api_keys.txt"

# List of full names
names = [
    "Diptaman Debnath", "Prantik Nath", "Biprajit Paul", "Arun Jayaraman", "Gourab Chakraborty",
    "Soumojit Makar", "Soummyadeep Debnath", "Ayushi Saha", "Akash Debnath", "Shubham Sinha",
    "Vibek Prasad Bin", "Victor Bhattacharjee", "Sovajit Roy", "Md Masum Miah", "Sourav Das",
    "Arkajyoti Roy", "Sagar Deep Saha", "Dipayan Saha", "Argha Chakraborty", "Khwairakpam Prosenjit Singha",
    "Raj Sutradhar", "Trishna sen", "Suvosree Roy", "Maman Das", "admin"
]

def create_user(username, password):
    url = f"{BASE_URL}/create_user"
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            api_key = data['data']['api_key']
            print(f"✅ {username} created successfully!")
            print(f"   🔑 API Key: {data['data']['api_key']}")
            
            with open(output_file, "a") as f:
                f.write(f"{full_name} ({username}): {api_key}\n")
            
        else:
            print(f"❌ Failed to create user '{username}': {response.status_code}")
            print(f"   Reason: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception for user '{username}': {str(e)}")

if __name__ == "__main__":
    default_password = "default123"  # You can change or randomize this per user
    
    with open(output_file, "w") as f:
        f.write("API Keys for Users:\n\n")

    for full_name in names:
        # Convert full name to a username (e.g., diptaman_debnath)
        username = full_name.split(' ')[0].lower()
        create_user(username, default_password)
