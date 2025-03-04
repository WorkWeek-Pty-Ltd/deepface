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
- Custom domain: deepface.workweek.tech (with SSL certificate)

## Custom Domain Setup

The API is accessible at `deepface.workweek.tech`. The domain is configured with:

- CNAME record pointing to `deepface-workweek.fly.dev`
- Automatic SSL certificate provisioning via Let's Encrypt
- Full HTTPS support with TLS 1.3

To use the API with the custom domain, simply replace `deepface-workweek.fly.dev` with `deepface.workweek.tech` in your requests:

```python
# API endpoint with custom domain
url = "https://deepface.workweek.tech/verify"
```

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
    "img2": "https://raw.githubusercontent.com/serengil/deepface/master/tests/dataset/img2.jpg",
    "model_name": "Facenet512",     # Optional - default is VGG-Face
    "detector_backend": "retinaface", # Optional - default is opencv
    "distance_metric": "cosine",    # Optional - default is cosine
    "threshold": 0.43               # Optional - custom similarity threshold
}

# Make request
response = requests.post(url, json=payload, headers=headers)
result = response.json()
```

### Configuring Threshold Values

The threshold parameter determines when two faces are considered a match:

- For cosine similarity, lower values mean stricter matching (typical range: 0.2 to 0.5)
- Default thresholds vary by model and distance metric

Model-specific default thresholds for cosine distance:

- VGG-Face: 0.68
- Facenet: 0.40
- Facenet512: 0.30
- ArcFace: 0.68
- SFace: 0.593
- OpenFace: 0.10
- DeepFace: 0.23
- DeepID: 0.015
- GhostFaceNet: 0.65

You can customize this threshold based on your specific needs:

- Lower threshold = fewer false positives but more false negatives
- Higher threshold = more false positives but fewer false negatives

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

## Error Monitoring

The application uses Sentry for error tracking and performance monitoring:

- Real-time error tracking and reporting
- Performance monitoring with automatic transaction tracking
- Error context and stack traces
- Deployed to workweek-africa Sentry organization

### Sentry Configuration

The Sentry integration is configured via environment variables:

1. `SENTRY_DSN`: The Data Source Name for your Sentry project
2. Automatic instrumentation for Flask applications
3. Performance monitoring enabled with traces and profiles

For local development, ensure the `SENTRY_DSN` is set in your `.env` file.

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

## Gotchas

### Dependency Management

This repository uses a specific structure for managing dependencies, inherited from the upstream DeepFace repository:

- `requirements_local`: Contains pinned versions of core ML dependencies that are known to work with DeepFace. These versions have been tested and verified by the original developers. **Do not remove this file** as it ensures compatibility between critical ML components.
- `requirements.txt`: Contains API and web service dependencies.
- `requirements_additional.txt`: Contains additional ML model dependencies.
- `requirements_test.txt`: Contains testing-specific dependencies. This file was made by us, not the original DeepFace repository. It is used to test the API.

The Dockerfile installs these dependencies in a specific order to ensure compatibility:

1. Core ML dependencies from `requirements_local`
2. API dependencies from `requirements.txt`
3. Additional ML model dependencies from `requirements_additional.txt`

This structure is important because ML libraries often have strict version dependencies. The pinned versions in `requirements_local` prevent compatibility issues between core components like TensorFlow, Keras, and OpenCV.
