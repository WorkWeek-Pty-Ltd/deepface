import requests
import base64
import os
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://deepface-workweek.fly.dev"
API_KEY = os.environ.get("DEEPFACE_API_KEY")  # Get API key from environment variable

headers = {
    "X-API-Key": API_KEY
}

# Create a session for consistent connection handling
session = requests.Session()
session.verify = False  # Disable SSL verification for the session

def test_server_health():
    response = session.get(f"{API_URL}/", headers=headers)
    print(f"Server Status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.status_code == 200

def test_verify():
    if not test_server_health():
        print("Server is not healthy, skipping verification test")
        return

    # Open and encode the test images
    with open("tests/dataset/img1.jpg", "rb") as img1_file:
        img1_base64 = base64.b64encode(img1_file.read()).decode('utf-8')
    
    with open("tests/dataset/img2.jpg", "rb") as img2_file:
        img2_base64 = base64.b64encode(img2_file.read()).decode('utf-8')

    # Prepare the request payload
    payload = {
        "img1": img1_base64,
        "img2": img2_base64,
        "model_name": "VGG-Face",
        "detector_backend": "opencv",
        "distance_metric": "cosine",
        "align": True,
        "enforce_detection": True
    }

    try:
        # Make the verification request using the session
        response = session.post(
            f"{API_URL}/verify",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"\nVerification Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Raw Response: {response.text}")

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\nVerification Result: {result}")
            except Exception as e:
                print(f"Error parsing response: {e}")
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    test_verify() 