# Chainlit with Vertex AI Deployment

This repository contains a Chainlit application that uses Google's Vertex AI Discovery Engine for conversational search, along with a deployment script to deploy the application to Google Cloud Run.

## Prerequisites

Before deploying the application, ensure you have the following:

1. A Google Cloud project with the following APIs enabled:
   - Cloud Run API
   - Artifact Registry API
   - Discovery Engine API
   - Secret Manager API
2. A Discovery Engine data store set up in your Google Cloud project

### For Local Deployment

If deploying from your local machine, you'll also need:

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
2. [Docker](https://docs.docker.com/get-docker/) installed

### For Cloud Shell Deployment

You can also deploy directly from [Google Cloud Shell](https://shell.cloud.google.com/), which has all the necessary tools pre-installed. See the DEPLOYMENT_GUIDE.md for detailed instructions.

## Environment Variables

The application requires the following environment variables:

- `project_id`: Your Google Cloud project ID
- `location`: The location of your Discovery Engine data store (e.g., "global", "us", "eu")
- `data_store_id`: The ID of your Discovery Engine data store

## Deployment

The `deploy.sh` script automates the deployment process to Google Cloud Run. It handles:

1. Creating a service account with necessary permissions (if not provided)
2. Setting up an Artifact Registry repository
3. Building and pushing the Docker image
4. Deploying the application to Cloud Run with the required configuration

### Usage

Make the script executable:

```bash
chmod +x deploy.sh
```

Run the deployment script:

```bash
./deploy.sh PROJECT_ID [LOCATION] [DATA_STORE_ID] [SERVICE_NAME] [SERVICE_ACCOUNT]
```

Parameters:
- `PROJECT_ID` (required): Your Google Cloud project ID
- `LOCATION` (optional, default: "us-central1"): The region to deploy to
- `DATA_STORE_ID` (required): The ID of your Discovery Engine data store
- `SERVICE_NAME` (optional, default: "chainlit-vertex-app"): The name for your Cloud Run service
- `SERVICE_ACCOUNT` (optional): A custom service account to use. If not provided, one will be created

Example:

```bash
./deploy.sh my-project-id us-central1 my-data-store-id my-chainlit-app
```

### Service Account and Secret

The deployment script will:

1. Create a service account with the necessary permissions if one is not provided
2. Expect a secret named `chainlit-sa-key` containing the service account key

To set up the service account key and secret, use the provided `setup-secret.sh` script:

```bash
# Make the script executable
chmod +x setup-secret.sh

# Run the script with your project ID
./setup-secret.sh PROJECT_ID [SERVICE_ACCOUNT_NAME]
```

Parameters:
- `PROJECT_ID` (required): Your Google Cloud project ID
- `SERVICE_ACCOUNT_NAME` (optional, default: "chainlit-vertex-sa"): The name of the service account

The script will:
1. Create a service account key
2. Create a secret named `chainlit-sa-key` in Secret Manager
3. Grant the service account access to the secret
4. Clean up temporary files

Alternatively, you can create the secret manually:

```bash
# Create a service account key
gcloud iam service-accounts keys create key.json --iam-account=SERVICE_ACCOUNT_EMAIL

# Create a secret with the key
gcloud secrets create chainlit-sa-key --data-file=key.json

# Delete the local key file for security
rm key.json
```

## Cloud Run Configuration

The deployment configures the Cloud Run service with:

- Memory: 2GB
- CPU: 1
- Min instances: 0 (scales to zero)
- Max instances: 2
- Timeout: 3600s (1 hour)
- Public access (--allow-unauthenticated)

You can modify these settings in the `deploy.sh` script if needed.

## Local Development

To run the application locally:

```bash
export project_id=YOUR_PROJECT_ID
export location=YOUR_LOCATION
export data_store_id=YOUR_DATA_STORE_ID
chainlit run chainlit-with-vertex-basic.py
```
