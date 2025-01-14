# 3rd parth dependencies
from flask import Flask, request
from flask_cors import CORS
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import os
import socket
import threading

# project dependencies
from deepface import DeepFace
from deepface.api.src.modules.core.routes import blueprint
from deepface.commons.logger import Logger

logger = Logger()

def before_send(event, hint):
    # Add custom tags and context
    if event.get('request'):
        event['tags'] = {
            'endpoint': request.endpoint,
            'method': request.method,
            'api_version': DeepFace.__version__
        }
    return event

def tcp_health_server():
    # Create a TCP socket server for health checks
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5001))
    server.listen(1)
    
    while True:
        try:
            client, addr = server.accept()
            client.send(b'healthy\n')
            client.close()
        except Exception as e:
            logger.error(f"TCP Health Check Error: {e}")
            continue

def create_app():
    # Initialize Sentry with performance monitoring
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,  # Capture 100% of transactions for performance monitoring
        before_send=before_send,
        release=f"deepface@{DeepFace.__version__}"  # Track releases using DeepFace version
    )

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(blueprint)
    logger.info(f"Welcome to DeepFace API v{DeepFace.__version__}!")

    # Start TCP health check server in a separate thread
    tcp_thread = threading.Thread(target=tcp_health_server, daemon=True)
    tcp_thread.start()
    logger.info("TCP health check server started on port 5001")

    return app
