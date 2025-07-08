#!/bin/bash
# run.sh - Entry point for the 100x Productivity Analyzer on Replit

# Install dependencies
echo "Installing dependencies..."
pip install -r 100x-Productivity-Analyzer/requirements.txt

# Set the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/100x-Productivity-Analyzer

# Run the application
echo "Starting 100x Productivity Analyzer..."
cd 100x-Productivity-Analyzer
python main.py