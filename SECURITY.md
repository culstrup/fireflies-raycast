# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in FlyCast, please report it by creating an issue on GitHub marked [SECURITY].

Alternatively, you can email any security concerns directly to the maintainer. Please provide detailed information about the vulnerability, including:

1. Steps to reproduce
2. Potential impact
3. Suggestions for remediation if you have them

## API Key Security

FlyCast uses an API key for authentication with the Fireflies.ai API. Keep your API key secure:

1. Never share your API key publicly
2. Store it only in your local `.env` file (which is ignored by git)
3. If you suspect your key has been compromised, regenerate it immediately in your Fireflies.ai account

## Best Practices for Users

- Keep your FlyCast installation and dependencies up-to-date
- Review the code before running it, especially if you've forked or modified it
- Be cautious when adding functionality that extends the permissions or access scopes of the application
