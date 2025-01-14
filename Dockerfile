# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.8.12
LABEL org.opencontainers.image.source="https://github.com/serengil/deepface"

# -----------------------------------
# create required folder
RUN mkdir -p /app && chown -R 1001:0 /app
RUN mkdir /app/deepface

# -----------------------------------
# switch to application directory
WORKDIR /app

# -----------------------------------
# update image os and install system dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libhdf5-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------
# Copy requirements files first to leverage Docker cache
COPY requirements_local /app/requirements_local.txt
COPY requirements.txt /app/requirements.txt
COPY requirements_additional.txt /app/requirements_additional.txt

# Install dependencies in a single layer
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r /app/requirements_local.txt && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r /app/requirements.txt && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -r /app/requirements_additional.txt

# -----------------------------------
# Copy the rest of the application code
COPY ./deepface /app/deepface
COPY ./package_info.json /app/
COPY ./setup.py /app/
COPY ./README.md /app/
COPY ./entrypoint.sh /app/deepface/api/src/entrypoint.sh

# Install the local package
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org -e .

# -----------------------------------
# Set working directory and expose port
WORKDIR /app/deepface/api/src
EXPOSE 5000

ENTRYPOINT [ "sh", "entrypoint.sh" ]
