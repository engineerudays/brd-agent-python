#!/bin/bash
# Run the Streamlit frontend

# Change to the project root directory
cd "$(dirname "$0")/.."

# Run Streamlit
streamlit run frontend/app.py --server.port 8501

