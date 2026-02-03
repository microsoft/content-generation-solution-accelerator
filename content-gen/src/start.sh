#!/bin/bash

# Start the Content Generation Solution Accelerator

echo "Starting Content Generation Solution Accelerator..."

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run with hypercorn for production
hypercorn app:app \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers ${WORKERS:-4} \
    --access-log - \
    --error-log -
