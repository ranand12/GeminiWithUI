# Deploying to Cloud Run using Google Cloud Shell

This guide provides specific instructions for deploying your Chainlit application to Google Cloud Run using Google Cloud Shell.

## Why Use Cloud Shell?

Google Cloud Shell provides several advantages for deployment:

1. No need to install Google Cloud SDK or Docker locally
2. Pre-authenticated with your Google Cloud account
3. Uses Cloud Build for container building, which is more reliable than local Docker
4. Free to use and accessible from any browser

## Step 1: Open Cloud Shell

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the Cloud Shell icon (>_) in the top-right corner of the console
3. Wait for Cloud Shell to initialize

## Step 2: Clone or Upload Your Application

### Option A: Clone from Git Repository

If your code is in a Git repository:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/VertexAI-Basic-Chainlit
```

### Option B: Upload Files Directly

1. Click on the "Open Editor" button in Cloud Shell (pencil icon)
2. Use File > Upload to upload your application files:
   - chainlit-with-vertex-basic.py
   - requirements.txt
   - Dockerfile
   - chainlit.md
   - deploy.sh
   - setup-secret.sh
   - Any other necessary files

## Step 3: Enable Required APIs

```bash
# Set your project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"

# Enable required APIs
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  discoveryengine.googleapis.com \
  cloudbuild.googleapis.com \
  --project=$PROJECT_ID
```

## Step 4: Make Scripts Executable

```bash
chmod +x deploy.sh setup-secret.sh
```

## Step 5: Set Up Service Account and Secret

```bash
# Replace with your actual project ID
PROJECT_ID=$(gcloud config get-value project)

# Create the service account and set up the secret
./setup-secret.sh $PROJECT_ID
```

This script will:
1. Create a service account named "chainlit-vertex-sa" if it doesn't exist
2. Grant the necessary roles to the service account
3. Create a service account key
4. Store the key in Secret Manager as "chainlit-sa-key"
5. Grant the service account access to the secret

> **Note on Permissions**: You need sufficient permissions in your Google Cloud project to create service accounts, assign IAM roles, and manage secrets. If you encounter permission errors, the script will provide guidance on what permissions you need or what actions to take. You may need to ask your project administrator for help if you don't have the required permissions.
>
> Required roles for this step:
> - `Service Account Admin` (to create service accounts)
> - `Project IAM Admin` (to assign roles)
> - `Secret Manager Admin` (to create and manage secrets)

## Step 6: Deploy to Cloud Run

```bash
# Replace with your actual project ID and data store ID
PROJECT_ID=$(gcloud config get-value project)
LOCATION="us-central1"
DATA_STORE_ID="your-data-store-id"  # Replace with your actual data store ID
SERVICE_NAME="chainlit-vertex-app"

# Run the deployment script
./deploy.sh $PROJECT_ID $LOCATION $DATA_STORE_ID $SERVICE_NAME
```

## Step 7: Access Your Application

After deployment completes, the script will output the URL of your deployed application. Click on this URL to open your application in a new browser tab.

## Troubleshooting

### Check Deployment Status

```bash
gcloud run services describe $SERVICE_NAME \
  --region=$LOCATION \
  --project=$PROJECT_ID
```

### View Logs

```bash
gcloud run services logs read $SERVICE_NAME \
  --region=$LOCATION \
  --project=$PROJECT_ID
```

### Check Build Status

If the build fails:

```bash
gcloud builds list --project=$PROJECT_ID
```

To see detailed logs for a specific build:

```bash
gcloud builds log BUILD_ID --project=$PROJECT_ID
```

## Updating Your Deployment

To update your deployment after making changes:

1. Make your changes to the application files in Cloud Shell Editor
2. Run the deployment script again with the same parameters

```bash
./deploy.sh $PROJECT_ID $LOCATION $DATA_STORE_ID $SERVICE_NAME
```

The script will build a new Docker image with a new tag and update your Cloud Run service.
