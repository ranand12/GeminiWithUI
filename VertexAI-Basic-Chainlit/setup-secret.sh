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
  
  # Try to create the service account, but handle potential permission errors
  if ! gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="Chainlit Vertex AI Service Account" \
    --project="$PROJECT_ID" 2>/tmp/sa_error; then
    
    echo "Failed to create service account. This might be due to insufficient permissions."
    echo "Error details: $(cat /tmp/sa_error)"
    echo ""
    echo "You have two options:"
    echo "1. Ask your project administrator to create the service account for you with the following roles:"
    echo "   - roles/discoveryengine.viewer"
    echo "   - roles/discoveryengine.admin"
    echo "   - roles/secretmanager.secretAccessor"
    echo ""
    echo "2. If you have the 'Owner' or 'Service Account Admin' role, try running this command manually:"
    echo "   gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --project=$PROJECT_ID"
    echo ""
    exit 1
  fi
  
  # Add necessary roles to the service account
  echo "Granting necessary roles to service account..."
  
  # Try to add roles, but handle potential permission errors
  if ! gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/discoveryengine.viewer" 2>/tmp/role_error; then
    
    echo "Failed to grant discoveryengine.viewer role. This might be due to insufficient permissions."
    echo "Error details: $(cat /tmp/role_error)"
    echo ""
    echo "You may need to ask your project administrator to grant the following roles to the service account:"
    echo "   - roles/discoveryengine.viewer"
    echo "   - roles/discoveryengine.admin"
    echo ""
    # Continue with the script, as we might still be able to create the key
  fi
  
  if ! gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/discoveryengine.admin" 2>/tmp/role_error; then
    
    echo "Failed to grant discoveryengine.admin role. This might be due to insufficient permissions."
    echo "Error details: $(cat /tmp/role_error)"
    echo ""
    # Continue with the script, as we might still be able to create the key
  fi
  
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
  if ! gcloud secrets versions add chainlit-sa-key \
    --data-file="$KEY_FILE" \
    --project="$PROJECT_ID" 2>/tmp/secret_error; then
    
    echo "Failed to add new version to secret. This might be due to insufficient permissions."
    echo "Error details: $(cat /tmp/secret_error)"
    echo ""
    echo "You may need to ask your project administrator to grant you the 'Secret Manager Admin' role."
    echo ""
    exit 1
  fi
else
  echo "Creating secret 'chainlit-sa-key'..."
  if ! gcloud secrets create chainlit-sa-key \
    --data-file="$KEY_FILE" \
    --project="$PROJECT_ID" 2>/tmp/secret_error; then
    
    echo "Failed to create secret. This might be due to insufficient permissions."
    echo "Error details: $(cat /tmp/secret_error)"
    echo ""
    echo "You may need to ask your project administrator to grant you the 'Secret Manager Admin' role."
    echo ""
    exit 1
  fi
fi

# Grant the service account access to the secret
echo "Granting the service account access to the secret..."
if ! gcloud secrets add-iam-policy-binding chainlit-sa-key \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID" 2>/tmp/binding_error; then
  
  echo "Failed to grant secretmanager.secretAccessor role. This might be due to insufficient permissions."
  echo "Error details: $(cat /tmp/binding_error)"
  echo ""
  echo "You may need to ask your project administrator to grant the service account access to the secret."
  echo ""
  # Continue with the script, as we've already created the key and secret
fi

# Clean up
rm -rf "$TEMP_DIR"
echo "Secret setup completed successfully!"
echo "The service account key has been stored in Secret Manager as 'chainlit-sa-key'."
echo "You can now deploy your application using the deploy.sh script."
