#!/bin/bash
set -e

# Check if running in Cloud Shell
if [ -n "$CLOUD_SHELL" ]; then
  echo "Running in Google Cloud Shell"
  # Cloud Shell is already authenticated with gcloud
else
  echo "Running in local environment"
  # Local environment might need additional authentication
fi

# Default values
DEFAULT_PROJECT_ID=$(gcloud config get-value project)
DEFAULT_SERVICE_ACCOUNT_NAME="chainlit-vertex-sa"

# Parse command line arguments
PROJECT_ID=${1:-$DEFAULT_PROJECT_ID}
SERVICE_ACCOUNT_NAME=${2:-$DEFAULT_SERVICE_ACCOUNT_NAME}

# Validate required parameters
if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required"
  echo "Usage: $0 PROJECT_ID [SERVICE_ACCOUNT_NAME]"
  exit 1
fi

SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists, create it if it doesn't
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
  echo "Service account $SERVICE_ACCOUNT does not exist. Creating it now..."
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
  
  echo "Service account created successfully."
else
  echo "Using existing service account: $SERVICE_ACCOUNT"
fi

# Create a temporary directory for the key
TEMP_DIR=$(mktemp -d)
KEY_FILE="$TEMP_DIR/key.json"

echo "Creating service account key for $SERVICE_ACCOUNT..."
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SERVICE_ACCOUNT" \
  --project="$PROJECT_ID"

# Check if the secret already exists
if gcloud secrets describe chainlit-sa-key --project="$PROJECT_ID" &>/dev/null; then
  echo "Secret 'chainlit-sa-key' already exists. Adding a new version..."
  gcloud secrets versions add chainlit-sa-key \
    --data-file="$KEY_FILE" \
    --project="$PROJECT_ID"
else
  echo "Creating secret 'chainlit-sa-key'..."
  gcloud secrets create chainlit-sa-key \
    --data-file="$KEY_FILE" \
    --project="$PROJECT_ID"
fi

# Grant the service account access to the secret
echo "Granting the service account access to the secret..."
gcloud secrets add-iam-policy-binding chainlit-sa-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID"

# Clean up
rm -rf "$TEMP_DIR"
echo "Secret setup completed successfully!"
echo "The service account key has been stored in Secret Manager as 'chainlit-sa-key'."
echo "You can now deploy your application using the deploy.sh script."
