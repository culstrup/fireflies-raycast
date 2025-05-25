#!/bin/bash

# Fireflies Raycast Extension Setup Script

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up Fireflies Raycast Extension...${NC}"

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${BLUE}Creating Python virtual environment...${NC}"
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment. Please ensure you have the 'venv' module installed.${NC}"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    echo "FIREFLIES_API_KEY=\"your-api-key-here\"" > .env
fi

# Ask for Fireflies API key
echo -e "${BLUE}Do you want to set up your Fireflies API key now? (y/n)${NC}"
read -r answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Please enter your Fireflies API key:${NC}"
    read -r api_key

    # Update .env file with the provided API key
    sed -i.bak "s/FIREFLIES_API_KEY=\"your-api-key-here\"/FIREFLIES_API_KEY=\"$api_key\"/" .env
    rm -f .env.bak

    echo -e "${GREEN}API key saved to .env file.${NC}"
else
    echo -e "${BLUE}You can manually edit the .env file later to add your API key.${NC}"
fi

# Make scripts executable
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x *.py
chmod +x *.sh

echo -e "${GREEN}Setup complete!${NC}"

# Instructions for adding to Raycast
echo -e "\n${BLUE}To add these scripts to Raycast:${NC}"
echo -e "1. Open Raycast"
echo -e "2. Go to Extensions > Script Commands"
echo -e "3. Click 'Add Script Directory'"
echo -e "4. Select this directory: $(pwd)"
echo -e "\n${BLUE}To use the scripts, you need to:${NC}"
echo -e "1. Open System Preferences > Security & Privacy > Privacy > Accessibility"
echo -e "2. Add Raycast to the list of apps allowed to control your computer"
echo -e "\n${GREEN}Enjoy your Fireflies integration!${NC}"
