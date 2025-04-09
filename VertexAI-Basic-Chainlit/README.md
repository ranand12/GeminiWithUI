# Chainlit with Vertex AI Deployment

This repository contains a Chainlit application that uses Google's Vertex AI Discovery Engine for conversational search, along with a simplified deployment script to deploy the application to Google Cloud Run.

## Deployment from Google Cloud Shell

The easiest way to deploy this application is directly from Google Cloud Shell:

1. Open [Google Cloud Shell](https://shell.cloud.google.com/)
2. Clone this repository or upload the files
3. Navigate to the project directory
4. Run the deployment script

```bash
# Clone the repository (if using Git)
git clone https://github.com/your-username/your-repo.git
cd your-repo/VertexAI-Basic-Chainlit

# Make the script executable
chmod +x deploy.sh

# Deploy the application
./deploy.sh YOUR_PROJECT_ID YOUR_DATA_STORE_ID
```

## Prerequisites

Before deploying the application, ensure you have the following:

1. A Google Cloud account with billing enabled
2. A Discovery Engine data store set up in your Google Cloud project
3. Required permissions:
   - Artifact Registry Administrator
   - Cloud Build Editor
   - Cloud Run Admin
   - Service Account User

## Environment Variables

The application requires the following environment variables:

- `project_id`: Your Google Cloud project ID
- `location`: The location of your Discovery Engine data store (e.g., "global", "us", "eu")
- `data_store_id`: The ID of your Discovery Engine data store

## Simplified Deployment

This project uses Cloud Build for a streamlined deployment process. The deployment script handles:

1. Creating an Artifact Registry repository (if it doesn't exist)
2. Enabling required Google Cloud APIs
3. Building and pushing the Docker image
4. Deploying the application to Cloud Run

### Usage

Make the script executable:

```bash
chmod +x deploy.sh
```

Run the deployment script:

```bash
./deploy.sh PROJECT_ID DATA_STORE_ID [REGION] [SERVICE_NAME]
```

Parameters:
- `PROJECT_ID` (required): Your Google Cloud project ID
- `DATA_STORE_ID` (required): The ID of your Discovery Engine data store
- `REGION` (optional, default: "us-central1"): The region to deploy to
- `SERVICE_NAME` (optional, default: "chainlit-vertex-app"): The name for your Cloud Run service

Example:

```bash
./deploy.sh my-project-id my-data-store-id
```

## Deployment Process

The deployment process consists of the following steps:

1. The script checks if the Artifact Registry repository exists and creates it if needed
2. Required Google Cloud APIs are enabled
3. Cloud Build builds the Docker image and pushes it to Artifact Registry
4. Cloud Run service is deployed with the specified environment variables

## Troubleshooting

### Build Failures

If the build fails, check the Cloud Build logs:

```bash
gcloud builds list --project=PROJECT_ID
gcloud builds log BUILD_ID --project=PROJECT_ID
```

### Deployment Issues

If the deployment fails, check the Cloud Run logs:

```bash
gcloud run services logs read SERVICE_NAME --region=REGION --project=PROJECT_ID
```

### Permission Issues

Ensure your account has the necessary permissions:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

## Local Development

To run the application locally:

```bash
export project_id=YOUR_PROJECT_ID
export location=YOUR_LOCATION
export data_store_id=YOUR_DATA_STORE_ID
chainlit run chainlit-with-vertex-basic.py
```
