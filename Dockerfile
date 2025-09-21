# Stage 1: Build the React Frontend
FROM node:18-alpine AS builder
WORKDIR /app/console
COPY console/package.json console/package-lock.json ./
RUN npm install
COPY console/ .
RUN npm run build

# Stage 2: Set up the Python Backend and Serve the Frontend
FROM python:3.9-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# --- NEW: Explicitly set the Hugging Face cache directory ---
# This tells libraries to use a writable directory inside our app folder.
ENV HF_HOME=/app/.cache

# Create and set permissions for the Hugging Face cache
RUN mkdir -p /app/.cache && chown -R 1000:1000 /app/.cache

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code
COPY . .
# Copy the built static files from the 'builder' stage
COPY --from=builder /app/console/dist ./console/dist

# Expose the port the app will run on
EXPOSE 7860

# The command to start the Gunicorn server with the correct Uvicorn worker
CMD ["gunicorn", "--preload", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:7860", "--timeout", "120", "main:app"]
