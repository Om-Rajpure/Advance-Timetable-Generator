#!/bin/bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Frontend dependencies and build
echo "Building Frontend..."
cd frontend
npm install
npm run build
cd ..
