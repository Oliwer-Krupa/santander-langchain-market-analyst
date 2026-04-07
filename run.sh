#!/bin/bash
set -e

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend (background)
echo "Starting FastAPI backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 2

# Start Streamlit UI
echo "Starting Streamlit UI on port 8501..."
streamlit run ui/streamlit_app.py --server.port 8501

# Cleanup
kill $BACKEND_PID 2>/dev/null
