# DeepFace API Integration Guide

## Overview

The DeepFace API is deployed at `deepface.workweek.tech` and provides powerful facial recognition and analysis capabilities. This guide will help you integrate the API into your applications.

## Authentication

All API endpoints (except health check) require authentication using an API key.

```python
headers = {
    'X-API-Key': 'your-api-key-here'
}
```

Contact the WorkWeek team to obtain an API key for your application.

## Base URL

```
https://deepface.workweek.tech
```

## Endpoints

### 1. Face Verification (`/verify`)

Compare two faces to determine if they belong to the same person.

**Request Format:**

```python
import requests

url = "https://deepface.workweek.tech/verify"
payload = {
    "img1": "https://example.com/image1.jpg",  # URL to first image
    "img2": "https://example.com/image2.jpg",  # URL to second image
    "model_name": "VGG-Face",                  # Optional, defaults to "VGG-Face"
    "detector_backend": "opencv",              # Optional, defaults to "opencv"
    "distance_metric": "cosine",               # Optional, defaults to "cosine"
    "align": True,                            # Optional, defaults to True
    "enforce_detection": True,                # Optional, defaults to True
    "anti_spoofing": False                   # Optional, defaults to False
}

response = requests.post(url, json=payload, headers=headers)
```

**Response Format:**

```json
{
  "verified": true,
  "distance": 0.2,
  "threshold": 0.4,
  "model": "VGG-Face",
  "detector_backend": "opencv",
  "similarity_metric": "cosine",
  "facial_areas": {
    "img1": { "x": 104, "y": 55, "w": 341, "h": 341 },
    "img2": { "x": 104, "y": 55, "w": 341, "h": 341 }
  }
}
```

### 2. Face Analysis (`/analyze`)

Analyze facial attributes including age, gender, emotion, and race.

**Request Format:**

```python
url = "https://deepface.workweek.tech/analyze"
payload = {
    "img": "https://example.com/image.jpg",
    "actions": ["age", "gender", "emotion", "race"],  # Optional, defaults to all
    "detector_backend": "opencv",                     # Optional
    "align": True,                                   # Optional
    "enforce_detection": True                        # Optional
}

response = requests.post(url, json=payload, headers=headers)
```

**Response Format:**

```json
{
  "results": [
    {
      "age": 30,
      "dominant_gender": "Man",
      "gender": {
        "Man": 99.99,
        "Woman": 0.01
      },
      "dominant_emotion": "neutral",
      "emotion": {
        "angry": 0.01,
        "disgust": 0.0,
        "fear": 0.01,
        "happy": 0.01,
        "neutral": 99.95,
        "sad": 0.01,
        "surprise": 0.01
      },
      "dominant_race": "white",
      "race": {
        "asian": 0.01,
        "indian": 0.01,
        "black": 0.01,
        "white": 99.95,
        "middle eastern": 0.01,
        "latino hispanic": 0.01
      }
    }
  ]
}
```

### 3. Face Representation (`/represent`)

Extract facial embeddings that can be used for face recognition tasks.

**Request Format:**

```python
url = "https://deepface.workweek.tech/represent"
payload = {
    "img": "https://example.com/image.jpg",
    "model_name": "Facenet",                # Optional, defaults to "VGG-Face"
    "detector_backend": "opencv",           # Optional
    "enforce_detection": True,              # Optional
    "align": True,                         # Optional
    "anti_spoofing": False                 # Optional
}

response = requests.post(url, json=payload, headers=headers)
```

**Response Format:**

```json
{
    "results": [{
        "embedding": [...],  // Array of facial embedding values
        "face_confidence": 0.99,
        "facial_area": {
            "x": 104,
            "y": 55,
            "w": 341,
            "h": 341
        }
    }]
}
```

## Image Input Formats

The API supports multiple ways to provide images:

1. **URL (Recommended)**

   ```json
   { "img": "https://example.com/image.jpg" }
   ```

2. **Base64 Encoded**

   ```json
   { "img": "data:image/jpeg;base64,/9j/4AAQSkZJRg..." }
   ```

3. **Multipart Form Data**
   ```python
   files = {'img': open('image.jpg', 'rb')}
   response = requests.post(url, files=files, headers=headers)
   ```

## Error Handling

The API uses standard HTTP status codes:

- `200`: Successful request
- `400`: Bad Request (invalid input data)
- `401`: Unauthorized (missing or invalid API key)
- `503`: Service Unavailable (try again later)

Error responses include a descriptive message:

```json
{
  "error": "Invalid image format provided"
}
```

## Performance Considerations

1. **Response Times**

   - Average response times range from 1-4 seconds depending on the operation
   - Face verification typically takes longer than single-face analysis

2. **Rate Limiting**

   - The API implements rate limiting to ensure fair usage
   - Contact the WorkWeek team for rate limit details

3. **Best Practices**
   - Use URL inputs for better performance
   - Implement retry logic with exponential backoff for 503 responses
   - Cache facial embeddings when doing multiple comparisons
   - Optimize image sizes before sending (recommended max: 1920x1080)

## Monitoring and Debugging

The API includes Sentry integration for error tracking. If you encounter issues:

1. Check the response status code and error message
2. Ensure your API key is valid
3. Verify the image format and accessibility
4. Contact support with the timestamp and endpoint details

## Health Check

Monitor API availability using the health check endpoint:

```python
response = requests.get("https://deepface.workweek.tech/health")
assert response.status_code == 200
```

This endpoint doesn't require authentication and returns:

```json
{
  "status": "healthy"
}
```

For additional support or to report issues, please contact the WorkWeek team.
