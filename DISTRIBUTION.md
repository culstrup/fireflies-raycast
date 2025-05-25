# Distribution Checklist

Before packaging FlyCast for distribution on Gumroad or GitHub, make sure:

## Files to Include:
- [x] Python scripts:
  - `fetch_fireflies_from_chrome_tabs.py`
  - `fireflies_clipboard.py`
- [x] Shell scripts:
  - `fetch-fireflies-from-chrome-tabs.sh`
  - `copy-latest-fireflies-transcript.sh`
  - `setup.sh`
- [x] Configuration files:
  - `requirements.txt`
  - `.env.example`
- [x] Documentation:
  - `README.md`

## Files to Exclude:
- [ ] `.env` file (do not include your personal API key)
- [ ] `debug.log` (clean the repository of any logs)
- [ ] Any personal configuration files

## Final Steps:
1. Test the setup script on a clean environment
2. Make sure all hardcoded paths are removed
3. Verify that the script works when installed in different locations
4. Create a zip archive of the repository for Gumroad distribution

## Gumroad Setup:
1. Create a new product on Gumroad
2. Upload the zip file
3. Set your price (or "Pay what you want")
4. Write a compelling product description using content from the README
5. Add screenshots of FlyCast in action
6. Provide clear setup instructions

## GitHub Setup (Alternative):
1. Create a new GitHub repository
2. Push the clean codebase to the repository
3. Create a proper README with installation instructions
4. Consider adding screenshots in a `/screenshots` directory
5. Link to the GitHub repository from your Gumroad product or vice versa
