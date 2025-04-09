# Deployment Guide for Chainlit with Vertex AI

This guide provides step-by-step instructions for deploying your Chainlit application to Google Cloud Run, either from your local machine or directly from Google Cloud Shell.

## Prerequisites

Before you begin, make sure you have:

1. A Google Cloud account with billing enabled
2. A Discovery Engine data store set up in your Google Cloud project

### For Local Deployment

If deploying from your local machine, you'll also need:

1. Google Cloud SDK installed and configured on your local machine
2. Docker installed on your local machine

### For Cloud Shell Deployment

If deploying from Google Cloud Shell, you don't need to install any additional software as Cloud Shell comes with:

1. Google Cloud SDK pre-installed and authenticated
2. Support for building containers via Cloud Build

## Step 1: Enable Required APIs

Enable the necessary Google Cloud APIs:

```bash
# Set your project ID
PROJECT_ID=your-project-id

# Enable required APIs
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  discoveryengine.googleapis.com \
  --project=$PROJECT_ID
```

## Step 2: Prepare Your Application

Ensure your application files are ready:

1. `chainlit-with-vertex-basic.py` - The main application file
2. `requirements.txt` - Dependencies
3. `Dockerfile` - Container configuration
4. `chainlit.md` - Chainlit configuration

## Step 3: Set Up Service Account and Secret

Run the `setup-secret.sh` script to create a service account key and store it in Secret Manager:

```bash
# Make the script executable
chmod +x setup-secret.sh

# Run the script
./setup-secret.sh your-project-id
```

This script will:
1. Create a service account key for the "chainlit-vertex-sa" service account
2. Store the key in Secret Manager as "chainlit-sa-key"
3. Grant the service account access to the secret

## Step 4: Deploy to Cloud Run

### Option A: Deploying from Google Cloud Shell

1. Open [Google Cloud Shell](https://shell.cloud.google.com/)

2. Clone your repository or upload the application files:
   ```bash
   # If your code is in a Git repository:
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   
   # Or upload files directly to Cloud Shell using the Cloud Shell Editor
   # Click on the "Open Editor" button in Cloud Shell, then use File > Upload
   ```

3. Make the deployment scripts executable:
   ```bash
   chmod +x deploy.sh setup-secret.sh
   ```

4. Run the deployment script:
   ```bash
   ./deploy.sh your-project-id us-central1 your-data-store-id chainlit-vertex-app
   ```

   The script will automatically detect that it's running in Cloud Shell and use Cloud Build instead of local Docker for building the container image.

### Option B: Deploying from Local Machine

Run the `deploy.sh` script to build and deploy your application:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the script
./deploy.sh your-project-id us-central1 your-data-store-id chainlit-vertex-app
```

Parameters for both deployment options:
- `your-project-id`: Your Google Cloud project ID
- `us-central1`: The region to deploy to (can be changed)
- `your-data-store-id`: The ID of your Discovery Engine data store
- `chainlit-vertex-app`: The name for your Cloud Run service (can be changed)

## Step 5: Verify Deployment

After the deployment completes, the script will output the URL of your deployed application. Open this URL in a web browser to verify that your application is running correctly.

## Troubleshooting

### Service Account Permissions

If you encounter permission issues, ensure your service account has the following roles:
- `roles/discoveryengine.viewer`
- `roles/discoveryengine.admin`
- `roles/secretmanager.secretAccessor`

You can add these roles manually:

```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:chainlit-vertex-sa@your-project-id.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.viewer"
```

### Container Issues

If your container fails to start, check the Cloud Run logs:

```bash
gcloud run services logs read chainlit-vertex-app \
  --region=us-central1 \
  --project=your-project-id
```

### Secret Access

If your application cannot access the secret, verify that:
1. The secret exists: `gcloud secrets list --project=your-project-id`
2. The service account has access to the secret: 
   ```bash
   gcloud secrets get-iam-policy chainlit-sa-key \
     --project=your-project-id
   ```

## Updating Your Deployment

To update your deployment after making changes to your application:

1. Make your changes to the application files
2. Run the `deploy.sh` script again with the same parameters

The script will build a new Docker image with a new tag, push it to Artifact Registry, and update your Cloud Run service.

## Cleaning Up

If you want to remove your deployment:

```bash
# Delete the Cloud Run service
gcloud run services delete chainlit-vertex-app \
  --region=us-central1 \
  --project=your-project-id

# Delete the service account
gcloud iam service-accounts delete chainlit-vertex-sa@your-project-id.iam.gserviceaccount.com \
  --project=your-project-id

# Delete the secret
gcloud secrets delete chainlit-sa-key \
  --project=your-project-id
```
