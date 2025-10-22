# Plex Recommendations - Examples and Demo Scripts

This directory contains example scripts and configuration templates for the Plex Recommendations system.

## Directory Structure

- `demo-scripts/` - Demo and testing scripts
- `config-templates/` - Configuration templates and examples

## Demo Scripts

### `generate-admin-url.py`
Generates secure admin URLs for accessing the feedback system.

**Usage:**
```bash
python3 examples/demo-scripts/generate-admin-url.py
```

### `deploy-feedback-system.sh`
Deploys the complete feedback system with Lambda and website.

**Usage:**
```bash
./examples/demo-scripts/deploy-feedback-system.sh
```

### `test-system.py`
Tests all system components (Plex, TMDB, S3, Lambda).

**Usage:**
```bash
python3 examples/demo-scripts/test-system.py
```

### `force-website-refresh.sh`
Forces a complete refresh of the website and recommendations.

**Usage:**
```bash
./examples/demo-scripts/force-website-refresh.sh
```

## Configuration Templates

### `env-template.txt`
Template for environment variables configuration.

**Setup:**
1. Copy `config-templates/env-template.txt` to `.env` in the project root
2. Fill in your actual values
3. Never commit the `.env` file to version control

## Security Notes

- All demo scripts use environment variables for sensitive data
- Never hardcode API keys, tokens, or credentials
- Use the configuration templates as starting points
- Always change default admin keys and secrets

## Getting Started

1. Copy the environment template: `cp examples/config-templates/env-template.txt .env`
2. Fill in your configuration values
3. Run the test script to verify setup: `python3 examples/demo-scripts/test-system.py`
4. Deploy the system: `./examples/demo-scripts/deploy-feedback-system.sh`
