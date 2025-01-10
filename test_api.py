import requests
import os
import urllib3
import time
from typing import Dict, Any
import sys
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://deepface-workweek.fly.dev"
API_KEY = os.environ.get("DEEPFACE_API_KEY")  # Get API key from environment variable

if not API_KEY:
    print("Error: DEEPFACE_API_KEY environment variable not set")
    print("Please create a .env file with your API key or set it in your environment")
    sys.exit(1)

headers = {
    "X-API-Key": API_KEY
}

# Create a session for consistent connection handling
session = requests.Session()
session.verify = False  # Disable SSL verification for the session

def test_server_health() -> bool:
    """Test the server health endpoint"""
    try:
        response = session.get(f"{API_URL}/", headers=headers)
        print(f"Server Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error testing server health: {e}")
        return False

def test_authentication():
    """Test authentication scenarios"""
    print("\n=== Testing Authentication ===")
    
    # Test without API key
    try:
        response = requests.post(f"{API_URL}/verify")
        print(f"No API Key Test - Status: {response.status_code}")
        assert response.status_code == 401, "Should return 401 without API key"
        print("✓ No API key test passed")
    except AssertionError as e:
        print(f"✗ No API key test failed: {e}")
    except Exception as e:
        print(f"Error testing no API key: {e}")
    
    # Test with invalid API key
    try:
        invalid_headers = {"X-API-Key": "invalid_key"}
        response = requests.post(f"{API_URL}/verify", headers=invalid_headers, verify=False)
        print(f"Invalid API Key Test - Status: {response.status_code}")
        assert response.status_code == 401, "Should return 401 with invalid API key"
        print("✓ Invalid API key test passed")
    except AssertionError as e:
        print(f"✗ Invalid API key test failed: {e}")
    except Exception as e:
        print(f"Error testing invalid API key: {e}")

def get_github_raw_url(path: str) -> str:
    """Convert a local test image path to a GitHub raw URL"""
    # Remove 'tests/' prefix if it exists
    if path.startswith('tests/'):
        path = path[6:]
    return f"https://raw.githubusercontent.com/serengil/deepface/master/tests/{path}"

def test_verify(img1_path: str, img2_path: str, expected_match: bool | None = None) -> Dict[str, Any]:
    """Test face verification with given images"""
    if not test_server_health():
        print("Server is not healthy, skipping verification test")
        return {}

    img1_url = get_github_raw_url(img1_path)
    img2_url = get_github_raw_url(img2_path)

    payload = {
        "img1": img1_url,
        "img2": img2_url,
        "model_name": "VGG-Face",
        "detector_backend": "opencv",
        "distance_metric": "cosine",
        "align": True,
        "enforce_detection": True
    }

    try:
        start_time = time.time()
        response = session.post(
            f"{API_URL}/verify",
            json=payload,
            headers=headers,
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        print(f"Response Time: {elapsed_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if expected_match is not None:
                assert result.get("verified") == expected_match, f"Expected match={expected_match}, got {result.get('verified')}"
            return result
        else:
            print(f"Error: {response.text}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return {}

def test_error_cases():
    """Test various error cases"""
    print("\n=== Testing Error Cases ===")
    
    # Test with invalid image URL
    payload = {
        "img1": "https://invalid-url/image.jpg",
        "img2": "https://invalid-url/image.jpg"
    }
    try:
        response = session.post(f"{API_URL}/verify", json=payload, headers=headers, verify=False)
        print(f"Invalid Image Test - Status: {response.status_code}")
        assert response.status_code == 400, "Should return 400 with invalid image data"
        print("✓ Invalid image test passed")
    except AssertionError as e:
        print(f"✗ Invalid image test failed: {e}")
    except Exception as e:
        print(f"Error testing invalid image: {e}")
    
    # Test with missing required fields
    payload = {"img1": get_github_raw_url("dataset/img1.jpg")}
    try:
        response = session.post(f"{API_URL}/verify", json=payload, headers=headers, verify=False)
        print(f"Missing Field Test - Status: {response.status_code}")
        assert response.status_code == 400, "Should return 400 with missing fields"
        print("✓ Missing field test passed")
    except AssertionError as e:
        print(f"✗ Missing field test failed: {e}")
    except Exception as e:
        print(f"Error testing missing fields: {e}")

def performance_test():
    """Run performance tests with different image sizes"""
    print("\n=== Running Performance Tests ===")
    
    test_cases = [
        ("dataset/img1.jpg", "dataset/img2.jpg", "Same person test (should match)", True),
        ("dataset/img1.jpg", "dataset/img3.jpg", "Different person test (should not match)", False),
        ("dataset/img20.jpg", "dataset/img21.jpg", "Same person test 2 (should match)", True),
        ("dataset/img16.jpg", "dataset/img17.jpg", "Same person test 3 (should match)", True)
    ]
    
    for img1_path, img2_path, test_name, expected_match in test_cases:
        print(f"\nRunning {test_name}")
        start_time = time.time()
        result = test_verify(img1_path, img2_path, expected_match)
        elapsed_time = time.time() - start_time
        print(f"Total time: {elapsed_time:.2f} seconds")
        if result:
            print(f"Result: {json.dumps(result, indent=2)}")
        else:
            print("Test failed - no result")

def main():
    """Run all tests"""
    print("Starting API Tests...")
    
    # Basic health check
    if not test_server_health():
        print("Server health check failed, aborting tests")
        sys.exit(1)
    
    # Run all test suites
    test_authentication()
    test_error_cases()
    performance_test()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 