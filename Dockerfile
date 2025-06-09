# Stage 1: Build stage to build Llama.cpp
FROM python:3.12.7-slim-bookworm as builder

# Install build dependencies for Llama.cpp and ffmpeg for audio extraction
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.12.7-slim-bookworm

# Install ffmpeg for audio extraction
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements
COPY --from=builder /root/.local /root/.local

# Copy the app
COPY . .

# Copy the .env template
COPY .env.template .env

CMD ["sh"]