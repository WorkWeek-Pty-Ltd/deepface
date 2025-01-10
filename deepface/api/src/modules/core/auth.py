import os
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.environ.get('API_KEY')
        if not api_key:
            return jsonify({"error": "Server configuration error"}), 500
        
        # Check if API key is in headers
        auth_header = request.headers.get('X-API-Key')
        if not auth_header:
            return jsonify({"error": "No API key provided"}), 401
        
        if auth_header != api_key:
            return jsonify({"error": "Invalid API key"}), 401
            
        return f(*args, **kwargs)
    return decorated_function 