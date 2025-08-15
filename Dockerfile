# Stage 1: Build the React Frontend (if you were deploying a UI)
# For now, we are only deploying the Hub, so this is not needed.

# Stage 2: Set up the Python Backend
FROM python:3.9-slim
WORKDIR /app
ENV PYTHONUNBUFFERed=1

# --- NEW LINE: Create and set permissions for the Hugging Face cache ---
RUN mkdir -p /app/.cache && chown -R 1000:1000 /app/.cache
# --------------------------------------------------------------------

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code
COPY . .

# Expose the port the app will run on (Hugging Face sets this)
EXPOSE 7860

# The command to start the Gunicorn server
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "main:app"]
