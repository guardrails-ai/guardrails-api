FROM public.ecr.aws/docker/library/python:3.12-slim

# Accept a build arg for the Guardrails token
# We'll add this to the config using the configure command below
ARG GUARDRAILS_TOKEN

# Create app directory
WORKDIR /app

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

# Set the directory for nltk data
ENV NLTK_DATA=/opt/nltk_data

# Set env vars for server
ENV GR_CONFIG_FILE_PATH="sample-config.py"
ENV GR_ENV_FILE=".env"
ENV PORT=8000

# print the version just to verify
RUN python3 --version
# start the virtual environment
RUN python3 -m venv /opt/venv

# Install some utilities
RUN apt-get update && \
    apt-get install -y git pkg-config curl gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements*.txt .

# Install app dependencies
# If you use Poetry this step might be different
RUN pip install -r requirements-lock.txt

# Download punkt data
RUN python -m nltk.downloader -d /opt/nltk_data punkt

# Run the Guardrails configure command to create a .guardrailsrc file
RUN guardrails configure --enable-metrics --enable-remote-inferencing  --token $GUARDRAILS_TOKEN

# Install any validators from the hub you want
RUN guardrails hub install hub://guardrails/detect_pii --no-install-local-models && \
    guardrails hub install hub://guardrails/competitor_check --no-install-local-models

# Fetch AWS RDS cert
RUN curl https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o ./global-bundle.pem

# Copy the rest over
# We use a .dockerignore to keep unwanted files exluded
COPY . .

EXPOSE ${PORT}

# This is our start command; yours might be different.
# The guardrails-api is a standard FastAPI application.
# You can use whatever production server you want that support FastAPI.
# Here we use gunicorn
CMD uvicorn --factory 'guardrails_api.app:create_app' --host 0.0.0.0 --port ${PORT} --timeout-keep-alive=90 --workers=4