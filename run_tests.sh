#!/bin/sh

# Start Ollama in background
ollama serve &

# Optional: wait a bit for Ollama to become responsive
sleep 2

python3 -m unittest ${@}