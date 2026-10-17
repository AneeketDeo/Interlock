#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-rca-sentinel-cup-2026}"
REGION="${GCP_LOCATION:-us-central1}"
SERVICE_NAME="rca-sentinel-backend"
SPANNER_INSTANCE="${SPANNER_INSTANCE_ID:-rca-sentinel-graph}"
SPANNER_DB="${SPANNER_DATABASE_ID:-rca_db}"
PUBSUB_TOPIC="${PUBSUB_TOPIC_ID:-telemetry-ingest-topic}"
BQ_DATASET="${BIGQUERY_DATASET:-rca_sentinel}"

echo "================================================================="
echo " Deploying RCA-Sentinel to Google Cloud Run (AI Builder Cup 2026)"
echo " Project: ${PROJECT_ID} | Region: ${REGION}"
echo "================================================================="

# 1. Enable Required GCP APIs
echo "[1/4] Enabling required GCP APIs..."
gcloud services enable \
    spanner.googleapis.com \
    pubsub.googleapis.com \
    bigquery.googleapis.com \
    aiplatform.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}"

# 2. Build Container Image with Cloud Build
echo "[2/4] Building container image via Cloud Build..."
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/rca-images/${SERVICE_NAME}:latest"
gcloud builds submit --tag "${IMAGE_TAG}" ./backend --project="${PROJECT_ID}"

# 3. Deploy Backend Microservice to Cloud Run
echo "[3/4] Deploying Backend service to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_TAG}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --max-instances=10 \
    --set-env-vars="APP_ENV=prod,GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true,SPANNER_INSTANCE_ID=${SPANNER_INSTANCE},SPANNER_DATABASE_ID=${SPANNER_DB},SPANNER_GRAPH_NAME=FactoryGraph,PUBSUB_TOPIC_ID=${PUBSUB_TOPIC},BIGQUERY_DATASET=${BQ_DATASET},GEMINI_MODEL=gemini-2.5-flash,DRY_RUN=true" \
    --project="${PROJECT_ID}"

# 4. Status Check
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --project="${PROJECT_ID}" --format='value(status.url)')
echo "================================================================="
echo " RCA-Sentinel successfully deployed to Google Cloud Run!"
echo " Service Endpoint: ${SERVICE_URL}"
echo " Swagger Docs:     ${SERVICE_URL}/docs"
echo "================================================================="
