#!/bin/bash
set -e

ollama serve &

sleep 3

MODEL_NAME="gemma3:latest"

if ! ollama list | grep -q "$MODEL_NAME"; then
    echo "[Bootstrap] Pulling $MODEL_NAME model..."
    ollama pull $MODEL_NAME
else
    echo "[Bootstrap] $MODEL_NAME already installed."
fi

echo "[Bootstrap] Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000
