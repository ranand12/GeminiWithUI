FROM python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

# Set working directory
WORKDIR /app

# Install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install google-cloud-discoveryengine chainlit==1.0.401

# Copy application files
COPY chainlit-with-vertex-basic.py app.py
COPY chainlit.md chainlit.md
COPY public/ public/

# Create .chainlit directory
RUN mkdir -p /.chainlit

# Run the application
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8080"]
