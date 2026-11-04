#!/bin/sh
# Start the dashboard at http://127.0.0.1:8501. It runs from this folder so its config file is read.
# It calls the installed Streamlit directly, because `uv run` may contact PyPI to sync packages.
cd "$(dirname "$0")" || exit 1
PYTHONDONTWRITEBYTECODE=1 exec ../.venv/bin/python -m streamlit run app.py
