#!/bin/bash

# Setup script for AI Call Agent

echo "Setting up AI Call Agent..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p audio_cache
mkdir -p recordings

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Make sure Asterisk is running with ARI enabled"
echo "3. Initialize the database: python main.py --init-db"
echo "4. Run the agent: python main.py --campaign 'Fund Recovery' --leads example_leads.csv"
echo ""
