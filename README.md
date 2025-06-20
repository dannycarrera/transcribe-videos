# Video Transcription API

A FastAPI application for transcribing videos using OpenAI's Whisper model.

## Features

- Transcribe video files via a REST API
- Uses Whisper AI for accurate transcription
- Stores transcripts in ChromaDB with vector embeddings
- OpenAPI documentation available at `/docs`

## Installation

1. Clone this repository
2. Install the requirements:

```bash
pip install -r requirements.txt
```

3. Make sure you have ffmpeg installed on your system:

- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `apt-get install ffmpeg` or similar for your distribution

4. Make sure you have [Ollama](https://ollama.com/download) installed on your system:
- Pull the required model `ollama pull llama3.2:1b-instruct-q2_K`

## Usage

### Start the API server

```bash
python run.py
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

## Development

### Project Structure

```
app/
├── __init__.py
├── main.py                 # FastAPI application
├── schemas/                # Pydantic schemas for API
│   ├── __init__.py
│   └── transcription.py
├── routers/                # API routes
│   ├── __init__.py
│   └── transcription.py
└── services/               # Business logic
    ├── __init__.py
    └── transcription_service.py
```

### Running Tests

```bash
python -m unittest
```

# Docker Dev Env

## Running tests

This command builds a docker image with the code of this repository and runs the repository's tests

```sh
./build_docker.sh my_app
docker run -t my_app ./run_tests.sh
```

## Running a specific test

This example runs a single test in the class TestTranscriptionService, with the name "test_create_transcript_success"

```sh
./build_docker.sh my_app
docker run -t my_app ./run_tests.sh app.tests.test_transcription_service.TestTranscriptionService.test_create_transcript_success
```