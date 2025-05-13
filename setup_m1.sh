#!/bin/bash

# Setup script for Buddy on M1 Macs
echo "Setting up Buddy for M1 Mac..."

# Check if brew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install portaudio
echo "Installing portaudio..."
brew install portaudio

# Create virtual environment
echo "Creating Python 3.11 virtual environment..."
python3.11 -m venv venv_py311
source venv_py311/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools==65.5.0
pip install -r requirements.txt

# Install spaCy language model
echo "Installing spaCy language model..."
python -m spacy download en_core_web_sm

# Install sounddevice as fallback
echo "Installing fallback dependencies..."
pip install sounddevice

echo "Setup complete! Activate the environment with: source venv_py311/bin/activate"