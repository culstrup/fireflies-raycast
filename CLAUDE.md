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

## Performance Notes

If script performance seems slow:

```bash
# Run with debug mode to see detailed progress
python fetch_fireflies_from_chrome_tabs.py --debug

# Check logs for slow API responses
tail -50 debug.log | grep "took"
```

The script uses parallel fetching with connection pooling to optimize performance. The main bottleneck is typically the Fireflies API response time, which can vary significantly (from 1s to 60s per transcript).

## CI Testing Notes

Tests use extensive mocking to prevent real network connections:

- Socket-level patching via sitecustomize.py
- Session and ThreadPoolExecutor mocking
- Timeouts to prevent infinite hanging

If tests are failing in CI, check:
- Mock configuration for any new API features
- Network isolation (tests shouldn't make real API calls)
- Concurrent execution handling