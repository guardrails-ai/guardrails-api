# FROM python:3.6
FROM public.ecr.aws/docker/library/python:3-slim

# Create app directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install app dependencies
RUN pip install -r requirements.txt

# start the virtual environment
RUN python3 -m venv venv

# Copy the whole folder inside the Image filesystem
COPY . .

EXPOSE 8000

CMD gunicorn --bind 0.0.0.0:8000 --timeout=5 --threads=10 wsgi:app
