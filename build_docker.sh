#!/bin/sh

export $(grep -v '^#' .env.template | xargs)
DOCKER_TAG=${1:-my-app}
DOCKER_DEFAULT_PLATFORM=linux/amd64

docker build --build-arg OLLAMA_MODEL=$OLLAMA_MODEL -t $DOCKER_TAG .