import time
import json
import logging
import pytest
from typing import Dict, Any
from .conftest import get_github_raw_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class TestHealth:
    def test_server_health(self, session, api_url, headers):
        """Test if the server is healthy by checking the health endpoint."""
        def check_health():
            response = session.get(f"{api_url}/health")
            if response.status_code != 200:
                logger.error(f"Health check failed with status code: {response.status_code}")
                return None
            
            # Also verify we can make an authenticated request
            minimal_payload = {
                "img1": get_github_raw_url("dataset/img1.jpg"),
                "img2": get_github_raw_url("dataset/img1.jpg")
            }
            response = session.post(f"{api_url}/verify", headers=headers, json=minimal_payload)
            if response.status_code in [200, 401]:  # Both success and auth failure are fine, means server is up
                return response
            elif response.status_code == 503:  # Service unavailable
                return None
            else:
                logger.error(f"Unexpected status code from verify endpoint: {response.status_code}")
                return None

        response = retry_with_backoff(check_health)
        assert response is not None, "Server health check failed"

class TestAuthentication:
    def test_no_api_key(self, session, api_url):
        """Test that requests without API key are rejected"""
        response = session.post(f"{api_url}/verify")
        assert response.status_code == 401, "Should return 401 without API key"

    def test_invalid_api_key(self, session, api_url):
        """Test that requests with invalid API key are rejected"""
        invalid_headers = {"X-API-Key": "invalid_key"}
        response = session.post(f"{api_url}/verify", headers=invalid_headers)
        assert response.status_code == 401, "Should return 401 with invalid API key"

class TestErrorCases:
    def test_invalid_image_url(self, session, api_url, headers):
        """Test that the API returns 400 for an invalid image URL."""
        response = session.post(
            f"{api_url}/verify",
            headers=headers,
            json={"img1": "invalid_url", "img2": get_github_raw_url("dataset/img1.jpg")},
        )
        assert response.status_code == 400

    def test_missing_fields(self, session, api_url, headers):
        """Test that the API returns 400 when required fields are missing."""
        response = session.post(
            f"{api_url}/verify",
            headers=headers,
            json={"img1": get_github_raw_url("dataset/img1.jpg")},  # Missing img2
        )
        assert response.status_code == 400

class TestVerification:
    @pytest.mark.parametrize("img1_path,img2_path,expected_match", [
        ("dataset/img1.jpg", "dataset/img2.jpg", True),
        ("dataset/img1.jpg", "dataset/img3.jpg", False),
        ("dataset/img20.jpg", "dataset/img21.jpg", True),
        ("dataset/img16.jpg", "dataset/img17.jpg", True)
    ])
    def test_face_verification(self, session, api_url, headers, img1_path, img2_path, expected_match):
        """Test face verification with different image pairs."""
        response = session.post(
            f"{api_url}/verify",
            headers=headers,
            json={
                "img1": get_github_raw_url(img1_path),
                "img2": get_github_raw_url(img2_path)
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["verified"] == expected_match

class TestPerformance:
    def test_cold_start(self, session, api_url, headers):
        """Test initial cold start response time"""
        start_time = time.time()
        response = session.get(f"{api_url}/", headers=headers)
        cold_start_time = time.time() - start_time
        logger.info(f"Cold start response time: {cold_start_time:.2f} seconds")
        assert response.status_code in [200, 404], f"Expected 200 or 404 status code, got {response.status_code}"

    def test_warm_requests(self, session, api_url, headers):
        """Test response times for warm requests"""
        warm_times = []
        for i in range(5):
            start_time = time.time()
            response = session.get(f"{api_url}/", headers=headers)
            request_time = time.time() - start_time
            warm_times.append(request_time)
            logger.info(f"Warm request {i+1} time: {request_time:.2f} seconds")
            assert response.status_code in [200, 404], f"Expected 200 or 404 status code, got {response.status_code}"
        
        avg_warm_time = sum(warm_times) / len(warm_times)
        logger.info(f"Average warm request time: {avg_warm_time:.2f} seconds") 