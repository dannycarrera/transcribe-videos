# Stage 1: pull the model using Ollama's official image
FROM ollama/ollama:latest AS builder

# Accept build argument
ARG OLLAMA_MODEL
ENV OLLAMA_MODEL=${OLLAMA_MODEL}

# Start Ollama, wait, then pull the model from env variable
RUN ollama serve & \
    sleep 3 && \
    ollama pull ${OLLAMA_MODEL} && \
    sleep 2

# Stage 2: create the app image
FROM python:3.12.7-slim-bookworm

# Install dependencies for Ollama runtime and ffmpeg for audio extraction
RUN apt-get update && apt-get install -y --no-install-recommends \
    fuse ca-certificates curl gnupg libssl-dev libstdc++6 libfuse2 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy Ollama binary and model data
COPY --from=builder /usr/bin/ollama /usr/bin/ollama
COPY --from=builder /root/.ollama /root/.ollama

WORKDIR /app

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY . .

# Copy the .env template
COPY .env.template .env

CMD ["sh"]