#!/usr/bin/env python
"""
Test script to verify that the custom threshold parameter works in the DeepFace API.
"""

import os
import requests
import json
import time

# Get API key from environment
API_KEY = os.getenv("DEEPFACE_API_KEY")
if not API_KEY:
    raise ValueError("DEEPFACE_API_KEY environment variable is not set")

# Set API URL - update with your actual API URL
API_URL = os.getenv("DEEPFACE_API_URL", "https://deepface-workweek.fly.dev")

# Test images from the DeepFace repo
IMG1_URL = "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img1.jpg"
IMG2_URL = "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img2.jpg"
# These images are of the same person

def test_threshold_parameter():
    """Test that the threshold parameter affects verification results."""
    
    # Test headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Base request payload
    base_payload = {
        "img1": IMG1_URL,
        "img2": IMG2_URL,
        "model_name": "Facenet512",
        "detector_backend": "retinaface",
        "distance_metric": "cosine",
        "align": True
    }
    
    # Test with default threshold
    print("Testing with default threshold...")
    response = requests.post(
        f"{API_URL}/verify", 
        json=base_payload, 
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    default_result = response.json()
    default_threshold = default_result["threshold"]
    default_distance = default_result["distance"]
    default_verified = default_result["verified"]
    
    print(f"Default threshold: {default_threshold}")
    print(f"Distance between faces: {default_distance}")
    print(f"Verified with default threshold: {default_verified}")
    
    # Now test with a very strict threshold that should fail
    strict_threshold = 0.1  # Very strict threshold that should cause verification to fail
    print(f"\nTesting with strict threshold ({strict_threshold})...")
    
    strict_payload = base_payload.copy()
    strict_payload["threshold"] = strict_threshold
    
    response = requests.post(
        f"{API_URL}/verify", 
        json=strict_payload, 
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    strict_result = response.json()
    strict_threshold_returned = strict_result["threshold"]
    strict_verified = strict_result["verified"]
    
    print(f"Requested threshold: {strict_threshold}")
    print(f"Returned threshold: {strict_threshold_returned}")
    print(f"Verified with strict threshold: {strict_verified}")
    
    # Now test with a very lenient threshold that should pass
    lenient_threshold = 0.9  # Very lenient threshold that should cause verification to pass
    print(f"\nTesting with lenient threshold ({lenient_threshold})...")
    
    lenient_payload = base_payload.copy()
    lenient_payload["threshold"] = lenient_threshold
    
    response = requests.post(
        f"{API_URL}/verify", 
        json=lenient_payload, 
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    lenient_result = response.json()
    lenient_threshold_returned = lenient_result["threshold"]
    lenient_verified = lenient_result["verified"]
    
    print(f"Requested threshold: {lenient_threshold}")
    print(f"Returned threshold: {lenient_threshold_returned}")
    print(f"Verified with lenient threshold: {lenient_verified}")
    
    # Verify that the threshold parameter is working correctly
    if strict_threshold_returned == strict_threshold and lenient_threshold_returned == lenient_threshold:
        print("\n✅ SUCCESS: Custom threshold values are being properly applied!")
    else:
        print("\n❌ FAILURE: Custom threshold values are not being properly applied")
    
    # Verify that the verification results are affected by the threshold
    if strict_verified is False and lenient_verified is True:
        print("✅ SUCCESS: Verification results are properly affected by threshold!")
    else:
        print("❌ FAILURE: Verification results are not properly affected by threshold")

if __name__ == "__main__":
    test_threshold_parameter() 