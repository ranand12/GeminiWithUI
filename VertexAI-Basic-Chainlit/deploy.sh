#!/bin/bash
set -e

# Ensure script is executable
if [ ! -x "$0" ]; then
  chmod +x "$0"
  echo "Made script executable"
fi

# Default values
DEFAULT_PROJECT_ID=$(gcloud config get-value project)
DEFAULT_REGION="us-central1"
DEFAULT_SERVICE_NAME="chainlit-vertex-app"
DEFAULT_REPOSITORY="chainlit-apps"

# Parse command line arguments
PROJECT_ID=${1:-$DEFAULT_PROJECT_ID}
DATA_STORE_ID=${2:-""}
REGION=${3:-$DEFAULT_REGION}
SERVICE_NAME=${4:-$DEFAULT_SERVICE_NAME}

# Print banner
echo "=================================================="
echo "  Chainlit Deployment to Cloud Run"
echo "  Project: $PROJECT_ID"
echo "  Data Store ID: $DATA_STORE_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "=================================================="

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: $0 PROJECT_ID DATA_STORE_ID [REGION] [SERVICE_NAME]"
  exit 1
fi

if [ -z "$DATA_STORE_ID" ]; then
  echo "Error: DATA_STORE_ID is required"
  echo "Usage: $0 PROJECT_ID DATA_STORE_ID [REGION] [SERVICE_NAME]"
  exit 1
fi

# Check if Artifact Registry repository exists, create if it doesn't
if ! gcloud artifacts repositories describe "$DEFAULT_REPOSITORY" \
  --location="$REGION" \
  --project="$PROJECT_ID" &>/dev/null; then
  echo "Creating Artifact Registry repository: $DEFAULT_REPOSITORY"
  gcloud artifacts repositories create "$DEFAULT_REPOSITORY" \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT_ID" \
    --description="Repository for Chainlit applications"
fi

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  discoveryengine.googleapis.com \
  --project="$PROJECT_ID"

# Submit the build to Cloud Build
echo "Submitting build to Cloud Build..."
gcloud builds submit \
  --project="$PROJECT_ID" \
  --config=cloudbuild.yaml \
  --substitutions=_REGION="$REGION",_SERVICE_NAME="$SERVICE_NAME",_REPOSITORY="$DEFAULT_REPOSITORY",_DATA_STORE_ID="$DATA_STORE_ID" \
  .

echo "Deployment submitted to Cloud Build."
echo "Check the build status at: https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
echo "Once deployed, your application will be available at: https://$SERVICE_NAME-<hash>.$REGION.run.app"
