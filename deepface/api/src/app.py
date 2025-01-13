# 3rd parth dependencies
from flask import Flask, request
from flask_cors import CORS
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import os

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
    return app
