import os
import sys
import time
import json
import urllib3
import requests
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get environment variables
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_BASE_URL", "https://deepface-workweek-dev.fly.dev")

if not API_KEY:
    logger.error("API_KEY environment variable not set")
    logger.error("Please create a .env file with your API key or set it in your environment")
    sys.exit(1)

# Default headers for API requests
headers = {
    "X-API-Key": API_KEY
}

# Create a session for connection pooling
session = requests.Session()
session.verify = False  # Disable SSL verification for the session

def retry_with_backoff(operation, max_retries=5):
    """
    Retry an operation with exponential backoff.
    Base delay is 10 seconds, which is multiplied by 3 for each retry.
    Returns the operation result or None if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            result = operation()
            if hasattr(result, 'status_code') and result.status_code != 503:
                return result
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed with error: {str(e)}")
        
        if attempt < max_retries - 1:  # Don't sleep after the last attempt
            delay = 10 * (3 ** attempt)  # 10s, 30s, 90s, 270s, 810s
            logger.info(f"Waiting {delay} seconds for retry...")
            time.sleep(delay)
    
    return None

def test_server_health():
    """Test if the server is healthy by checking the health endpoint."""
    def check_health():
        response = session.get(f"{API_URL}/health")
        if response.status_code != 200:
            logger.error(f"Health check failed with status code: {response.status_code}")
            return None
        
        # Also verify we can make an authenticated request
        minimal_payload = {
            "img1": get_github_raw_url("dataset/img1.jpg"),
            "img2": get_github_raw_url("dataset/img1.jpg")
        }
        response = session.post(f"{API_URL}/verify", headers=headers, json=minimal_payload)
        if response.status_code in [200, 401]:  # Both success and auth failure are fine, means server is up
            return response
        elif response.status_code == 503:  # Service unavailable
            return None
        else:
            logger.error(f"Unexpected status code from verify endpoint: {response.status_code}")
            return None

    response = retry_with_backoff(check_health)
    if not response:
        logger.error("Server health check failed, aborting tests")
        return False
    
    return True

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
        response = retry_with_backoff(
            lambda: session.post(
                f"{API_URL}/verify",
                json=payload,
                headers=headers,
                timeout=30
            )
        )
        elapsed_time = time.time() - start_time
        print(f"Response Time: {elapsed_time:.2f} seconds")
        
        if response:
            print(f"Status Code: {response.status_code}")
            result = response.json()
            if expected_match is not None:
                assert result.get("verified") == expected_match, f"Expected match={expected_match}, got {result.get('verified')}"
            return result
        else:
            print("Verify operation failed after retries")
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

def test_scaling():
    """Test scaling behavior of the API"""
    print("\n=== Testing Scaling Behavior ===")
    
    # Test initial cold start
    print("Testing cold start...")
    start_time = time.time()
    response = session.get(f"{API_URL}/", headers=headers)
    cold_start_time = time.time() - start_time
    print(f"Cold start response time: {cold_start_time:.2f} seconds")
    print(f"Cold start status code: {response.status_code}")

    # Test warm requests
    print("\nTesting warm requests...")
    warm_times = []
    for i in range(5):
        start_time = time.time()
        response = session.get(f"{API_URL}/", headers=headers)
        request_time = time.time() - start_time
        warm_times.append(request_time)
        print(f"Warm request {i+1} time: {request_time:.2f} seconds")
    
    avg_warm_time = sum(warm_times) / len(warm_times)
    print(f"\nAverage warm request time: {avg_warm_time:.2f} seconds")
    print(f"Cold start overhead: {cold_start_time - avg_warm_time:.2f} seconds")

    # Test scale down
    print("\nTesting scale down behavior...")
    print("Waiting 5 minutes for potential scale down...")
    time.sleep(300)  # Wait 5 minutes
    
    # Test scale up after scale down
    print("\nTesting scale up after idle...")
    start_time = time.time()
    response = session.get(f"{API_URL}/", headers=headers)
    scale_up_time = time.time() - start_time
    print(f"Scale up response time: {scale_up_time:.2f} seconds")
    print(f"Scale up status code: {response.status_code}")

def benchmark_timing():
    """Benchmark timing characteristics to validate health check settings"""
    print("\n=== Running Timing Benchmarks ===")
    
    # Test initial startup time (cold start)
    print("\nTesting cold start timing...")
    start_time = time.time()
    response = session.get(f"{API_URL}/", headers=headers)
    startup_time = time.time() - start_time
    print(f"Initial startup time: {startup_time:.2f}s")
    
    # Let the service settle
    time.sleep(2)
    
    # Test response times under rapid requests
    print("\nTesting rapid request response times...")
    rapid_times = []
    for i in range(10):
        start_time = time.time()
        response = session.get(f"{API_URL}/", headers=headers)
        request_time = time.time() - start_time
        rapid_times.append(request_time)
        print(f"Request {i+1}: {request_time:.2f}s")
        time.sleep(0.5)  # Small gap between requests
    
    # Test verify endpoint timing (more complex operation)
    print("\nTesting verify endpoint timing...")
    verify_times = []
    test_images = [
        ("dataset/img1.jpg", "dataset/img2.jpg"),
        ("dataset/img1.jpg", "dataset/img3.jpg")
    ]
    
    for img1, img2 in test_images:
        start_time = time.time()
        result = test_verify(img1, img2)
        verify_time = time.time() - start_time
        verify_times.append(verify_time)
        print(f"Verify operation: {verify_time:.2f}s")
    
    # Calculate and display statistics
    print("\n=== Timing Statistics ===")
    print(f"Cold start time: {startup_time:.2f}s")
    print(f"Average health check response: {sum(rapid_times)/len(rapid_times):.2f}s")
    print(f"Max health check response: {max(rapid_times):.2f}s")
    print(f"Average verify operation: {sum(verify_times)/len(verify_times):.2f}s")
    print(f"Max verify operation: {max(verify_times):.2f}s")
    
    # Recommendations
    print("\n=== Health Check Recommendations ===")
    max_response = max(rapid_times)
    if max_response > 5:
        print("⚠️ Consider increasing health check timeout (currently 5s)")
    if startup_time > 10:
        print("⚠️ Consider increasing grace period (currently 10s)")
    if max_response * 6 > 30:  # If max response time * 6 exceeds check interval
        print("⚠️ Consider increasing check interval (currently 30s)")

def main():
    """Run all tests"""
    print("Starting API Tests...")
    
    # Basic health check
    if not test_server_health():
        print("Server health check failed, aborting tests")
        sys.exit(1)
    
    # Run timing benchmarks first
    benchmark_timing()
    
    # Run other test suites
    test_authentication()
    test_error_cases()
    performance_test()
    test_scaling()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 