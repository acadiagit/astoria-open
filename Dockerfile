# Dockerfile – Nov 21 17:00 EST 
FROM python:3.9-slim

WORKDIR /app

# Torch CPU
RUN pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1

# Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# <<< THIS IS THE FIX – trailing slash on backend/ >>>
COPY . .

# UI
COPY console/dist ./console/dist

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
