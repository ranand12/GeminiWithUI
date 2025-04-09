# Deploying to Cloud Run using Google Cloud Shell

This guide provides specific instructions for deploying your Chainlit application to Google Cloud Run using Google Cloud Shell.

## Why Use Cloud Shell?

Google Cloud Shell provides several advantages for deployment:

1. No need to install Google Cloud SDK locally
2. Pre-authenticated with your Google Cloud account
3. Uses Cloud Build for container building
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
   - cloudbuild.yaml
   - deploy.sh
   - chainlit.md
   - Any other necessary files

## Step 3: Enable Required APIs

The deploy.sh script will handle this automatically, but if you want to enable them manually:

```bash
# Set your project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"

# Enable required APIs
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  discoveryengine.googleapis.com \
  --project=$PROJECT_ID
```

## Step 4: Make the Script Executable

```bash
chmod +x deploy.sh
```

## Step 5: Deploy to Cloud Run

```bash
# Replace with your actual project ID and data store ID
PROJECT_ID=$(gcloud config get-value project)
DATA_STORE_ID="your-data-store-id"  # Replace with your actual data store ID

# Run the deployment script
./deploy.sh $PROJECT_ID $DATA_STORE_ID
```

The script will:
1. Create an Artifact Registry repository if it doesn't exist
2. Enable required APIs
3. Submit the build to Cloud Build
4. Deploy to Cloud Run with the necessary environment variables

## Step 6: Monitor the Deployment

After submitting the deployment, you can monitor its progress:

```bash
# List recent builds
gcloud builds list --project=$PROJECT_ID

# View logs for a specific build
gcloud builds log BUILD_ID --project=$PROJECT_ID
```

## Step 7: Access Your Application

Once the deployment is complete, you can access your application at the URL provided in the deployment output. You can also find it in the Cloud Run console or by running:

```bash
gcloud run services describe chainlit-vertex-app \
  --region=us-central1 \
  --project=$PROJECT_ID \
  --format='value(status.url)'
```

## Troubleshooting

### Permission Issues

If you encounter permission issues, ensure your account has the necessary roles:

```bash
# Grant yourself the necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/iam.serviceAccountUser"
```

### Cloud Build Service Account Permissions

The Cloud Build service account may need additional permissions:

```bash
# Grant the Cloud Build service account permission to deploy to Cloud Run
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# Grant the Cloud Build service account permission to act as service accounts
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

## Updating Your Deployment

To update your deployment after making changes:

1. Make your changes to the application files in Cloud Shell Editor
2. Run the deployment script again with the same parameters

```bash
./deploy.sh $PROJECT_ID $DATA_STORE_ID
```

The script will build a new Docker image and update your Cloud Run service.
