# DeepFace API on Fly.io

This repository contains the deployment configuration for running the DeepFace API on Fly.io. DeepFace is a facial recognition library that provides various functionalities including face verification, recognition, and analysis.

## Features

- Face verification API endpoint (`/verify`)
- Face analysis API endpoint (`/analyze`)
- Face representation API endpoint (`/represent`)
- API key authentication for secure access
- Deployed on Fly.io with auto-scaling capabilities

## API Authentication

The API uses standard HTTP status codes for authentication:

- 401 Unauthorized: Returned when no API key is provided or when an invalid API key is used
- 400 Bad Request: Returned for invalid input data
- 200 OK: Successful requests

All endpoints except the health check (`/`) require a valid API key in the `X-API-Key` header.

### Important Notes

- All API endpoints (except health check) only accept POST requests
- Images can be sent as:
  - Direct URLs (recommended)
  - Base64 encoded strings
  - File uploads via multipart/form-data
  - Local file paths (when running locally)

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

# API endpoint
url = "https://deepface-workweek.fly.dev/verify"

# Request payload with image URLs
payload = {
    "img1": "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img1.jpg",
    "img2": "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img2.jpg"
}

# Make request
response = requests.post(url, json=payload, headers=headers)
result = response.json()
```

## Development

### Using Conda Environment (Recommended)

1. Create the Conda environment:

   ```bash
   conda env create -f environment.yml
   ```

2. Activate the environment:

   ```bash
   conda activate deepface-env
   ```

3. Set environment variables:

   ```bash
   export API_KEY=your-secret-key
   ```

4. Run the API: `python -m deepface.api`

### Alternative Setup (pip)

1. Install dependencies: `pip install -r requirements.txt`
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

## API Key Management

For development and testing:

1. The API key is managed through Fly.io secrets
2. View current secrets (will only show digests, not actual values):
   ```bash
   fly secrets list -a deepface-workweek
   ```
3. Generate a new API key:
   ```bash
   openssl rand -hex 32
   ```
4. Set a new API key:
   ```bash
   fly secrets set API_KEY=<new_key> -a deepface-workweek
   ```
5. For local testing, set the API key in your environment:
   ```bash
   export DEEPFACE_API_KEY=your-api-key
   ```
   Note: The actual API key value should be obtained securely from your team's secret management system, not from `fly secrets list` which only shows digests.

## Testing

Run the test suite to verify API functionality:

```bash
# Ensure API key is set in environment
export DEEPFACE_API_KEY=your-api-key

# Run tests
python test_api.py
```

The test suite verifies:

- API authentication
- Face verification functionality
- Error handling
- Performance metrics

### Test Notes

- Tests expect proper HTTP status codes (401 for auth failures, 400 for bad requests)
- Tests use direct image URLs from the GitHub repository for consistency
- Average response times range from 1-4 seconds depending on the operation
