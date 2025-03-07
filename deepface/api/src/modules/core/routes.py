# built-in dependencies
from typing import Union
import os

# 3rd party dependencies
from flask import Blueprint, request, jsonify
import numpy as np
import sentry_sdk

# project dependencies
from deepface import DeepFace
from deepface.api.src.modules.core import service
from deepface.commons import image_utils
from deepface.commons.logger import Logger
from deepface.api.src.modules.core.auth import require_api_key

logger = Logger()

blueprint = Blueprint("api", __name__)

# pylint: disable=no-else-return, broad-except


@blueprint.route("/")
@require_api_key
def home():
    return f"<h1>Welcome to DeepFace API v{DeepFace.__version__}!</h1>"


def extract_image_from_request(img_key: str) -> Union[str, np.ndarray]:
    """
    Extracts an image from the request either from json or a multipart/form-data file.

    Args:
        img_key (str): The key used to retrieve the image data
            from the request (e.g., 'img1').

    Returns:
        img (str or np.ndarray): Given image detail (base64 encoded string, image path or url)
            or the decoded image as a numpy array.
    """

    # Check if the request is multipart/form-data (file input)
    if request.files:
        # request.files is instance of werkzeug.datastructures.ImmutableMultiDict
        # file is instance of werkzeug.datastructures.FileStorage
        file = request.files.get(img_key)

        if file is None:
            raise ValueError(f"Request form data doesn't have {img_key}")

        if file.filename == "":
            raise ValueError(f"No file uploaded for '{img_key}'")

        img = image_utils.load_image_from_file_storage(file)

        return img
    # Check if the request is coming as base64, file path or url from json or form data
    elif request.is_json or request.form:
        input_args = request.get_json() or request.form.to_dict()

        if input_args is None:
            raise ValueError("empty input set passed")

        # this can be base64 encoded image, and image path or url
        img = input_args.get(img_key)

        if not img:
            raise ValueError(f"'{img_key}' not found in either json or form data request")

        return img

    # If neither JSON nor file input is present
    raise ValueError(f"'{img_key}' not found in request in either json or form data")


@blueprint.route("/represent", methods=["POST"])
@require_api_key
def represent():
    input_args = (request.is_json and request.get_json()) or (
        request.form and request.form.to_dict()
    )

    try:
        img = extract_image_from_request("img")
    except Exception as err:
        return {"exception": str(err)}, 400

    obj = service.represent(
        img_path=img,
        model_name=input_args.get("model_name", "VGG-Face"),
        detector_backend=input_args.get("detector_backend", "opencv"),
        enforce_detection=bool(input_args.get("enforce_detection", True)),
        align=bool(input_args.get("align", True)),
        anti_spoofing=bool(input_args.get("anti_spoofing", False)),
        max_faces=int(float(input_args["max_faces"])) if input_args.get("max_faces") else None,
    )

    logger.debug(obj)

    return obj


@blueprint.route("/verify", methods=["POST"])
@require_api_key
def verify():
    input_args = (request.is_json and request.get_json()) or (
        request.form and request.form.to_dict()
    )

    try:
        img1 = extract_image_from_request("img1")
    except Exception as err:
        return {"exception": str(err)}, 400

    try:
        img2 = extract_image_from_request("img2")
    except Exception as err:
        return {"exception": str(err)}, 400

    # Extract threshold parameter if provided
    # The threshold determines when two faces are considered a match
    # Lower values are stricter (fewer false positives)
    # Higher values are more lenient (fewer false negatives)
    threshold = None
    if "threshold" in input_args:
        try:
            threshold_value = input_args.get("threshold")
            if threshold_value is not None:
                threshold = float(threshold_value)
        except (ValueError, TypeError):
            return {"exception": "Threshold must be a valid float value"}, 400

    verification = service.verify(
        img1_path=img1,
        img2_path=img2,
        model_name=input_args.get("model_name", "VGG-Face"),
        detector_backend=input_args.get("detector_backend", "opencv"),
        distance_metric=input_args.get("distance_metric", "cosine"),
        align=bool(input_args.get("align", True)),
        enforce_detection=bool(input_args.get("enforce_detection", True)),
        anti_spoofing=bool(input_args.get("anti_spoofing", False)),
        threshold=threshold,
    )

    logger.debug(verification)

    return verification


@blueprint.route("/analyze", methods=["POST"])
@require_api_key
def analyze():
    input_args = (request.is_json and request.get_json()) or (
        request.form and request.form.to_dict()
    )

    try:
        img = extract_image_from_request("img")
    except Exception as err:
        return {"exception": str(err)}, 400

    actions = input_args.get("actions", ["age", "gender", "emotion", "race"])
    # actions is the only argument instance of list or tuple
    # if request is form data, input args can either be text or file
    if isinstance(actions, str):
        actions = (
            actions.replace("[", "")
            .replace("]", "")
            .replace("(", "")
            .replace(")", "")
            .replace('"', "")
            .replace("'", "")
            .replace(" ", "")
            .split(",")
        )

    demographies = service.analyze(
        img_path=img,
        actions=actions,
        detector_backend=input_args.get("detector_backend", "opencv"),
        enforce_detection=bool(input_args.get("enforce_detection", True)),
        align=bool(input_args.get("align", True)),
        anti_spoofing=bool(input_args.get("anti_spoofing", False)),
    )

    logger.debug(demographies)

    return demographies


def set_user_context():
    # Set user context from API key if available
    api_key = request.headers.get('X-API-Key')
    if api_key:
        with sentry_sdk.configure_scope() as scope:
            scope.set_user({'id': api_key})


@blueprint.before_request
def before_request():
    set_user_context()


@blueprint.after_request
def after_request(response):
    # Add custom headers for tracking
    response.headers['X-Version'] = os.getenv('APP_VERSION', 'unknown')
    return response


@blueprint.route("/test-sentry")
def test_sentry():
    # Add extra context for this error
    sentry_sdk.set_context("test_context", {
        "purpose": "verification",
        "type": "manual_test"
    })
    raise Exception("Test error to verify Sentry integration")


@blueprint.route("/health")
def health_check():
    """Health check endpoint for Fly.io that doesn't require authentication"""
    return jsonify({"status": "healthy"}), 200
