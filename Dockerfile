# Stage 1: Build the React Frontend
FROM node:18-alpine AS builder
WORKDIR /app/console
# Copy only package files first to leverage Docker cache
COPY console/package.json console/package-lock.json ./
RUN npm install
# Copy the rest of the UI source code
COPY console/ .
# Build the static files into the /dist folder
RUN npm run build

# Stage 2: Set up the Python Backend and Serve the Frontend
FROM python:3.9-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code
COPY . .

# Copy the built static files from the 'builder' stage into the correct location
COPY --from=builder /app/console/dist ./console/dist

# Expose the port the app will run on (Hugging Face uses 7860)
EXPOSE 7860

# The command to start the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "main:app"]
