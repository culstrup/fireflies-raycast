# Claude Development Notes

This document contains helpful information for developing FlyCast with Claude.

## Common Tasks

### Checking Script Status

```bash
# Check if Python virtual environment is active
echo $VIRTUAL_ENV

# Activate virtual environment if needed
source .venv/bin/activate

# List available commands
ls -la *.sh *.py
```

### Testing Scripts

```bash
# Run the fetch script (without paste)
python fetch_fireflies_from_chrome_tabs.py

# Run the clipboard script
python fireflies_clipboard.py
```

### Debugging

```bash
# Check log file
tail -50 debug.log

# Clear log file
echo "" > debug.log
```

## Development Guidelines

1. Keep scripts organized and well-commented
2. Use relative paths for all file operations
3. Add error handling for API requests
4. Respect user privacy - never log API keys
5. Follow PEP 8 style guidelines for Python code

## Project Structure

- `*.py` - Python scripts for core functionality
- `*.sh` - Raycast script wrappers
- `.env` - Environment file for API key (not committed)
- `requirements.txt` - Python dependencies

## Future Enhancements

- [ ] Add filtering by transcript date
- [ ] Add support for other browsers
- [ ] Improve error messages
- [ ] Add optional transcript formatting options