# DeepFace API on Fly.io

This repository contains the deployment configuration for running the DeepFace API on Fly.io. DeepFace is a facial recognition library that provides various functionalities including face verification, recognition, and analysis.

## Features

- Face verification API endpoint (`/verify`)
- Face analysis API endpoint (`/analyze`)
- Face representation API endpoint (`/represent`)
- API key authentication for secure access
- Deployed on Fly.io with auto-scaling capabilities

## Deployment Configuration

The application is deployed using the following configuration:

- Performance CPU (2 CPUs)
- 4GB RAM
- HTTPS enabled
- API key authentication

## Environment Variables

The following environment variables are required:

- `API_KEY`: Secret key for API authentication

## API Usage

To use the API, include your API key in the request headers:

```python
headers = {
    'X-API-Key': 'your-api-key-here'
}
```

### Example Request

```python
import requests
import base64

# API endpoint
url = "https://deepface-workweek.fly.dev/verify"

# Prepare images
with open("image1.jpg", "rb") as img1, open("image2.jpg", "rb") as img2:
    img1_base64 = base64.b64encode(img1.read()).decode('utf-8')
    img2_base64 = base64.b64encode(img2.read()).decode('utf-8')

# Request payload
payload = {
    "img1_path": img1_base64,
    "img2_path": img2_base64
}

# Make request
response = requests.post(url, json=payload, headers=headers)
result = response.json()
```

## Development

To run the API locally:

1. Install dependencies: `pip install deepface`
2. Set environment variables:
   ```bash
   export API_KEY=your-secret-key
   ```
3. Run the API: `python -m deepface.api`

## Deployment

To deploy updates:

1. Update configuration in `fly.toml` if needed
2. Run `fly deploy`

## Security

The API is secured with:

- API key authentication
- HTTPS enforcement
- Rate limiting (via Fly.io)
