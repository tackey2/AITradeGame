# AITradeGame - Open Source AI Trading Simulator

[English](README.md) | [中文](README_ZH.md)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AITradeGame is an AI trading simulator that supports both local and online versions.

Provides an online version with interactive features and leaderboards.

Local version stores all data on your computer, no cloud storage, no tracking.

Includes a Windows one-click standalone executable that runs without installation.

## Features

### Desktop Version (Local)

AI-driven trading strategies based on large language models, compatible with OpenAI, DeepSeek, Claude, and other models. Leveraged portfolio management with ECharts visualizations. 100% privacy with all data stored in local database. Trading fee configuration supported to simulate real trading environment.

**Latest Features (Week 3 - Exchange Integration):**
- 🔗 **Binance Exchange Integration**: Connect to real Binance exchange (testnet and mainnet)
- 🔑 **Credentials Management UI**: Secure management of API keys with visual status indicators
- ⚡ **Live Trading**: Execute real trades on Binance (supports testnet for safe testing)
- 🎯 **Trading Modes**: Separation of environment (simulation/live) and automation (manual/semi/full)
- 🛡️ **Safety First**: Testnet-first approach with clear warnings for mainnet
- 📊 **Real-time Status**: Visual indicators showing connection status and last validation

**Previous Features:**
- API Provider Management: Unified management of multiple AI service provider API configurations
- Smart Model Selection: Automatically fetch available model lists for each provider
- Aggregated View: View aggregated assets and performance comparison across all models
- System Settings: Configurable trading frequency and fee rates

### Online Version (Public)

Leaderboard functionality to compete with AI enthusiasts worldwide. Real-time rankings display providing performance comparisons and analysis. Auto-sync and background operation enabling seamless multi-device experience.

## Quick Start

### Try Online Version

Launch the online version at https://aitradegame.com without any installation.

### Desktop Version

Download AITradeGame.exe from GitHub releases. Double-click the executable to run. The interface will open automatically. Start adding AI models and begin trading.

Alternatively, clone the repository from GitHub. Install dependencies with pip install -r requirements.txt. Run the application with python app.py and visit http://localhost:5000.

### Docker Deployment

You can also run AITradeGame using Docker:

**Using docker-compose (recommended):**
```bash
# Build and start the container
docker-compose up -d

# Access the application at http://localhost:5000
```

**Using docker directly:**
```bash
# Build the image
docker build -t aitradegame .

# Run the container
docker run -d -p 5000:5000 -v $(pwd)/data:/app/data aitradegame

# Access the application at http://localhost:5000
```

The data directory will be created automatically to store the SQLite database. To stop the container, run `docker-compose down`.

## Configuration

### API Provider Setup
First, add AI service providers:
1. Click the "API Provider" button
2. Enter provider name, API URL, and API key
3. Manually input available models or click "Fetch Models" to auto-fetch
4. Click save to complete configuration

### Adding Trading Models
After configuring providers, add trading models:
1. Click the "Add Model" button
2. Select a configured API provider
3. Choose a specific model from the dropdown
4. Enter display name and initial capital
5. Click submit to start trading

### System Settings
Click the "Settings" button to configure:
- Trading Frequency: Control AI decision interval (1-1440 minutes)
- Trading Fee Rate: Commission rate per trade (default 0.1%)

## Supported AI Models

Supports all OpenAI-compatible APIs. This includes OpenAI models like gpt-4 and gpt-3.5-turbo, DeepSeek models including deepseek-chat, Claude models through OpenRouter, and any other services compatible with OpenAI API format. More protocols are being added.

## Usage

Start the server by running AITradeGame.exe or python app.py. Add AI model configuration through the web interface at http://localhost:5000. The system automatically begins trading simulation based on your configuration. Trading fees are charged for each open and close position according to the set rate, ensuring AI strategies operate under realistic cost conditions.

## Privacy and Security

All data is stored in the AITradeGame.db SQLite file in the same directory as the executable. No external servers are contacted except your specified AI API endpoints. No user accounts or login required - everything runs locally.

## Development

Development requires Python 3.9 or later. Internet connection is needed for market data and AI API calls.

Install all dependencies with: pip install -r requirements.txt

## Project Structure

```
AITradeGame/
├── docs/                    # Documentation
│   ├── user/               # User guides
│   ├── developer/          # Developer documentation
│   ├── phases/             # Phase completion docs
│   └── archive/            # Historical documentation
├── tests/                  # Test files
├── scripts/                # Utility scripts
├── templates/              # HTML templates
├── static/                 # CSS and JavaScript
├── app.py                  # Main Flask application
├── exchange_client.py      # Binance exchange integration
├── trading_modes.py        # Trading logic (simulation/live)
├── database_enhanced.py    # Enhanced database with credentials
└── README.md
```

### Key Documentation:
- **User Guides**: `docs/user/EXCHANGE_SETUP_GUIDE.md` - Complete setup walkthrough
- **Developer Docs**: `docs/developer/` - API documentation and contribution guide
- **Phase Docs**: `docs/phases/` - Detailed implementation documentation

## Contributing

Community contributions are welcome. See `docs/developer/CONTRIBUTING.md` for guidelines.

## Disclaimer

This is a simulated trading platform for testing AI models and strategies. It is not real trading and no actual money is involved. Always conduct your own research and analysis before making investment decisions. No warranties are provided regarding trading outcomes or AI performance.

## Links

Online version with leaderboard and social features: https://aitradegame.com

Desktop builds and releases: https://github.com/chadyi/AITradeGame/releases/tag/main

Source code repository: https://github.com/chadyi/AITradeGame
