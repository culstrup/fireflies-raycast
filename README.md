# Fireflies Raycast Extension

<div align="center">

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/culstrup/fireflies-raycast.svg)](https://github.com/culstrup/fireflies-raycast/stargazers)
[![Ko-fi](https://img.shields.io/badge/Support-Ko--fi-FF5E5B.svg)](https://ko-fi.com/culstrup)

</div>

Access your [Fireflies.ai](https://fireflies.ai) meeting transcripts directly from [Raycast](https://raycast.com)! This extension allows you to:

1. **Copy your latest transcript** to your clipboard with a single command
2. **Fetch transcripts from open Chrome tabs** and copy them to your clipboard

Perfect for quickly referencing meeting notes, summaries, and transcripts while working.

![Fireflies Raycast Demo](screenshots/demo.png)

*Note: Add your screenshots to the screenshots directory!*

## 🚀 Quick Setup

1. Download or clone this repository
2. Run the setup script:
   ```bash
   ./setup.sh
   ```
3. Enter your Fireflies API key when prompted (or add it to the `.env` file later)
4. Add the script directory to Raycast

## 📋 How to Get Your Fireflies API Key

1. Log in to your Fireflies.ai account
2. Go to [Settings > API](https://fireflies.ai/settings/api)
3. Generate a new API key
4. Copy the key and paste it when prompted during setup (or add to `.env` file)

## 🧩 Available Commands

Once installed, you'll have access to these commands in Raycast:

- **Fetch Fireflies Transcripts from Chrome**: Copies transcripts from open Chrome tabs
- **Copy Latest Fireflies Transcript**: Copies your most recent Fireflies transcript

## 🔧 Manual Setup (if not using setup.sh)

1. Clone or download this repository
2. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Fireflies API key:
   ```
   FIREFLIES_API_KEY="your-api-key-here"
   ```
4. Make the scripts executable:
   ```bash
   chmod +x *.py *.sh
   ```

## 📱 Raycast Integration

To add these scripts to Raycast:

1. Open Raycast
2. Go to Extensions > Script Commands
3. Click "Add Script Directory"
4. Select this directory

## 🔒 Enabling Paste Functionality

To enable automatic pasting:

1. Open System Preferences > Security & Privacy > Privacy > Accessibility
2. Add Raycast to the list of apps allowed to control your computer

## 💡 How It Works

- The scripts use the Fireflies GraphQL API to fetch your transcripts
- For Chrome tab fetching, it uses AppleScript to get URLs from Chrome tabs
- Transcripts are formatted and copied to your clipboard
- If accessibility permissions are granted, it can automatically paste content

## 📝 Requirements

- macOS (for AppleScript functionality)
- Python 3.6+
- Raycast
- Google Chrome
- Fireflies.ai account with API access

## 🔍 Troubleshooting

If you experience issues:
- Check the debug log at `debug.log` in the script directory
- Ensure your API key is correct in the `.env` file
- Verify that you've granted accessibility permissions to Raycast

## ❤️ Support This Project

If you find this extension useful, consider supporting its development:

- [Buy me a coffee on Ko-fi](https://ko-fi.com/culstrup)
- Star the repository on GitHub
- Share with other Fireflies users
- Contribute improvements via pull requests

Your support helps maintain and improve this tool!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.