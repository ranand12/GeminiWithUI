#!/bin/bash
set -e

# Check if running in Cloud Shell
if [ -n "$CLOUD_SHELL" ]; then
  echo "Running in Google Cloud Shell"
  # Cloud Shell specific configurations
  CLOUD_BUILD_OPTION="--platform=managed"
else
  echo "Running in local environment"
  # Local environment configurations
  CLOUD_BUILD_OPTION=""
fi

# Default values
DEFAULT_PROJECT_ID=$(gcloud config get-value project)
DEFAULT_LOCATION="us-central1"
DEFAULT_SERVICE_NAME="chainlit-vertex-app"
DEFAULT_MIN_INSTANCES=0
DEFAULT_MAX_INSTANCES=2
DEFAULT_MEMORY="2Gi"
DEFAULT_CPU=1
DEFAULT_TIMEOUT="3600s"

# Parse command line arguments
PROJECT_ID=${1:-$DEFAULT_PROJECT_ID}
LOCATION=${2:-$DEFAULT_LOCATION}
DATA_STORE_ID=${3:-""}
SERVICE_NAME=${4:-$DEFAULT_SERVICE_NAME}
SERVICE_ACCOUNT=${5:-""}

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: $0 PROJECT_ID [LOCATION] [DATA_STORE_ID] [SERVICE_NAME] [SERVICE_ACCOUNT]"
  exit 1
fi

if [ -z "$DATA_STORE_ID" ]; then
  echo "Error: DATA_STORE_ID is required"
  echo "Usage: $0 PROJECT_ID [LOCATION] [DATA_STORE_ID] [SERVICE_NAME] [SERVICE_ACCOUNT]"
  exit 1
fi

# If service account is not provided, create one
if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT_NAME="chainlit-vertex-sa"
  SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
  
  # Check if service account already exists
  if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
    echo "Creating service account: $SERVICE_ACCOUNT"
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
      --display-name="Chainlit Vertex AI Service Account" \
      --project="$PROJECT_ID"
    
    # Add necessary roles to the service account
    echo "Granting necessary roles to service account..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:$SERVICE_ACCOUNT" \
      --role="roles/discoveryengine.viewer"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
      --member="serviceAccount:$SERVICE_ACCOUNT" \
      --role="roles/discoveryengine.admin"
  else
    echo "Using existing service account: $SERVICE_ACCOUNT"
  fi
fi

# Set up Artifact Registry repository if it doesn't exist
REPO_NAME="chainlit-apps"
REPO_LOCATION="$LOCATION"

if ! gcloud artifacts repositories describe "$REPO_NAME" \
  --location="$REPO_LOCATION" \
  --project="$PROJECT_ID" &>/dev/null; then
  echo "Creating Artifact Registry repository: $REPO_NAME"
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REPO_LOCATION" \
    --project="$PROJECT_ID" \
    --description="Repository for Chainlit applications"
fi

# Set up Docker image name and tag
IMAGE_NAME="${REPO_LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# Build and push the Docker image
if [ -n "$CLOUD_SHELL" ]; then
  # Use Cloud Build when in Cloud Shell
  echo "Building and pushing Docker image using Cloud Build: $FULL_IMAGE_NAME"
  gcloud builds submit --tag="$FULL_IMAGE_NAME" \
    --project="$PROJECT_ID" \
    --timeout=30m .
else
  # Use local Docker when not in Cloud Shell
  echo "Building Docker image locally: $FULL_IMAGE_NAME"
  docker build -t "$FULL_IMAGE_NAME" .

  # Configure Docker to use gcloud as a credential helper
  gcloud auth configure-docker "${REPO_LOCATION}-docker.pkg.dev" --quiet

  # Push the Docker image to Artifact Registry
  echo "Pushing Docker image to Artifact Registry"
  docker push "$FULL_IMAGE_NAME"
fi

# Deploy to Cloud Run
echo "Deploying to Cloud Run: $SERVICE_NAME"
gcloud run deploy "$SERVICE_NAME" \
  --image="$FULL_IMAGE_NAME" \
  --platform=managed \
  --region="$LOCATION" \
  --project="$PROJECT_ID" \
  --service-account="$SERVICE_ACCOUNT" \
  --min-instances="$DEFAULT_MIN_INSTANCES" \
  --max-instances="$DEFAULT_MAX_INSTANCES" \
  --memory="$DEFAULT_MEMORY" \
  --cpu="$DEFAULT_CPU" \
  --timeout="$DEFAULT_TIMEOUT" \
  --port=8000 \
  --allow-unauthenticated \
  --set-env-vars="project_id=${PROJECT_ID},location=${LOCATION},data_store_id=${DATA_STORE_ID}" \
  --update-secrets="GOOGLE_APPLICATION_CREDENTIALS=/secrets/key.json:chainlit-sa-key:latest"

echo "Deployment completed successfully!"
echo "Your application is available at: $(gcloud run services describe $SERVICE_NAME --region=$LOCATION --project=$PROJECT_ID --format='value(status.url)')"
