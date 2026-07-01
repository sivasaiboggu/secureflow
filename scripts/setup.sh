#!/usr/bin/env bash
# SecureFlow CSPM Platform setup and initialization script
set -eo pipefail

echo "===================================================="
echo "🚀 SECUREFLOW CSPM PLATFORM INITIALIZATION"
echo "===================================================="

# 1. Prerequisite checks
echo "Checking system prerequisites..."
for cmd in python3 node npm docker docker-compose; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ Error: '$cmd' is not installed or not in PATH."
        exit 1
    fi
done
echo "✔ All core system dependencies verified."

# 2. Virtual Environment Setup
echo "Configuring Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "✔ Virtualenv successfully activated."

# 3. Installing dependencies
echo "Installing backend Python packages..."
pip install --upgrade pip
pip install -r backend/requirements.txt
echo "✔ Python packages installed."

# 4. Neural Network models training
echo "Starting AI/ML Neural network baseline training..."
python3 backend/app/ml/training/train_severity.py
python3 backend/app/ml/training/train_anomaly.py
echo "✔ Deep Learning models saved to ./models/ directory."

# 5. Database Initialization & Seeding
echo "Configuring PostgreSQL schemas and seeding baseline logs..."
# Using local sqlite default for immediate configuration if docker is not running yet
python3 scripts/seed_database.py
echo "✔ Baseline sandbox tenant structures initialized."

# 6. Docker container preparation
echo "Building Docker container assets..."
docker-compose build
echo "✔ Containers built successfully."

echo "===================================================="
echo "🎉 SETUP COMPLETED SUCCESSFULLY"
echo "===================================================="
echo "To launch the SecureFlow platform, run:"
echo "  docker-compose up"
echo ""
echo "Access the dashboard client at http://localhost:3000"
echo "API docs can be viewed at http://localhost:8000/api/docs"
echo "===================================================="
