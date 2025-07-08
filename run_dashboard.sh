#!/bin/bash
# run_dashboard.sh - Entry point for the 100x Productivity Analyzer Dashboard on Replit

# Install dependencies
echo "Installing dependencies..."
pip install -r 100x-Productivity-Analyzer/requirements.txt

# Set the Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/100x-Productivity-Analyzer

# Run the dashboard
echo "Starting 100x Productivity Analyzer Dashboard..."
cd 100x-Productivity-Analyzer
python dashboard-ui/run_dashboard.py