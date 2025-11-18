#!/bin/bash

# Stop any existing container
docker rm -f astoria-app 2>/dev/null

# Run the container with all necessary credentials and ports
echo "🚀 Starting Astoria Open..."
docker run --rm -it -p 7860:7860 \
  --name astoria-app \
  --env-file .env \
  --mount type=bind,source="$(pwd)/gcloud-service-key.json",target="/app/gcloud-service-key.json" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/gcloud-service-key.json" \
  astoria-open:latest
