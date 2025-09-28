# Kettle AI - AI-Powered Project Automation

Kettle is an AI-powered project automation tool that reads Slack messages, extracts coding tasks, and generates/modifies project code using LLMs. It now includes a background daemon that monitors IDE windows and shows a widget when you're coding.

## Features

- **Slack Integration**: Automatically fetches and processes Slack messages
- **Task Extraction**: Uses AI to extract actionable coding tasks from messages
- **Project Matching**: Finds similar existing projects using embeddings (MongoDB-powered)
- **Code Generation**: Generates and executes Python scripts for project setup
- **IDE Integration**: Background daemon that shows a widget when IDEs are active
- **Multi-LLM Support**: Works with Anthropic Claude, Google Gemini, and Perplexity AI
- **MongoDB Storage**: Fast, scalable project embedding storage with rich querying

## Quick Start

### 1. Setup MongoDB (Recommended)

For optimal performance, set up MongoDB for project embeddings:

```bash
# Install MongoDB (macOS with Homebrew)
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community

# Test MongoDB integration
python test_mongodb_integration.py

# Migrate existing JSON data to MongoDB
python migrate_to_mongodb.py
```

### 2. Setup Configuration

Run the daemon for the first time to configure your IDE paths:

```bash
python kettle_daemon.py
```

This will start an interactive configuration wizard where you can specify:
- Paths to your IDE applications (VSCode, PyCharm, Sublime Text)
- Slack check interval
- Auto-processing settings

### 3. Start the Daemon

```bash
python kettle_daemon.py
```

The daemon will:
- Run continuously in the background
- Monitor for IDE windows (VSCode, PyCharm, etc.)
- Show the Kettle widget when an IDE is active
- Automatically process new Slack messages
- Generate code based on extracted tasks

### 4. Using the Widget

When you open an IDE (like VSCode), a small ☕ widget will appear at the bottom right of your screen. Click it to see:

- Latest Slack message that triggered work
- Extracted tasks with phase indicators
- Generated script status
- Real-time updates

## Usage

### Manual Pipeline
```bash
python utils/master_pipeline.py
```

## Configuration

### MongoDB Configuration

Kettle AI uses MongoDB for storing project embeddings. Configure MongoDB connection:

```bash
# Environment variables (optional)
export MONGODB_URI="mongodb://localhost:27017/"
export MONGODB_DATABASE="kettle_ai"

# Or use default localhost connection
```

### Daemon Configuration

The daemon uses `json/kettle_config.json` for configuration:

```json
{
  "ide_applications": {
    "vscode": {
      "mac": "/Applications/Visual Studio Code.app",
      "windows": "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
      "linux": "code"
    }
  },
  "slack_check_interval": 30,
  "widget_check_interval": 2,
  "auto_process_slack": true
}
```

## File Structure

```
Kettle/
├── kettle_daemon.py          # Background daemon (main entry point)
├── mongodb_config.py         # MongoDB connection and embedding management
├── migrate_to_mongodb.py     # Migration script from JSON to MongoDB
├── test_mongodb_integration.py # MongoDB integration tests
├── utils/                    # Core utility modules
│   ├── master_pipeline.py        # Manual pipeline runner
│   ├── dashboard.py              # Widget UI
│   ├── extract_tasks.py          # Task extraction from messages
│   ├── execute_tasks.py          # Code generation and execution
│   ├── project_matcher.py        # Project similarity matching (MongoDB-powered)
│   ├── slack_fetch.py            # Slack message fetching
│   ├── kettle_monitor.py         # Background monitoring
│   ├── dependency_analyzer.py    # Task dependency analysis
│   ├── research_processor.py     # Research task processing
│   ├── json_utils.py             # JSON file utilities
│   ├── clear_json.py             # JSON cleanup utilities
│   ├── keys.py                   # API keys
│   └── prompts.py                # LLM prompts
├── json/                     # Data storage
│   ├── messages.json         # Slack messages
│   ├── coding_tasks.json     # Extracted coding tasks
│   ├── research_tasks.json   # Extracted research tasks
│   ├── writing_tasks.json    # Extracted writing tasks
│   ├── phased_tasks.json     # Hierarchical task structure
│   ├── task_dependencies.json # Task dependency matrix
│   ├── project_embeddings.json # Project similarity embeddings
│   ├── dependency_matrix.json # Dependency analysis results
│   ├── media.json            # Research media resources
│   ├── last_processed_ts.txt # Last processed timestamp
│   ├── last_task_processed_ts.txt # Last task processed timestamp
│   └── kettle_config.json    # Daemon configuration
├── gemini/                   # Google Gemini implementation
├── perplexity/               # Perplexity AI implementation
```

## Supported IDEs

- **Visual Studio Code**: Automatically detected on Mac, Windows, Linux
- **PyCharm**: JetBrains IDE support
- **Sublime Text**: Lightweight editor support
- **Custom**: Add your own IDE paths in the configuration

## LLM Providers

Kettle supports multiple LLM providers:

- **Anthropic Claude** (default): High-quality reasoning and code generation
- **Google Gemini**: Fast and cost-effective
- **Perplexity AI**: Alternative provider with different capabilities

## Widget Features

The Kettle widget provides:

- **Real-time Updates**: Shows latest work as it happens
- **Task Visualization**: Color-coded tasks by phase
- **Message Context**: Shows the Slack message that initiated work
- **Auto-hide**: Collapses after 5 seconds of inactivity
- **IDE Integration**: Only appears when coding in supported IDEs

## Troubleshooting

### MongoDB Connection Issues
- Ensure MongoDB is running: `brew services start mongodb/brew/mongodb-community`
- Test connection: `python test_mongodb_integration.py`
- Check MongoDB logs for errors
- Verify connection string in environment variables

### Widget Not Appearing
- Check that your IDE is in the configuration
- Ensure the daemon is running (`python kettle_daemon.py`)
- Verify IDE paths in `json/kettle_config.json`

### Slack Messages Not Processing
- Check your Slack API configuration in `utils/keys.py`
- Verify the channel ID in `utils/slack_fetch.py`
- Check the `auto_process_slack` setting in configuration

### Missing Dependencies
```bash
pip install sentence-transformers psutil requests pymongo
```

### IDE Integration Issues
- Verify IDE paths in `json/kettle_config.json`

### Project Similarity Not Working
- Run migration script: `python migrate_to_mongodb.py`
- Check MongoDB connection and data
- Verify project embeddings are being saved

## Development

To modify or extend Kettle:

1. **Add New LLM Provider**: Create a new directory with provider-specific files
2. **Customize Prompts**: Edit `utils/prompts.py` for different task extraction strategies
3. **Extend Widget**: Modify `utils/dashboard.py` for additional UI features
4. **Add IDE Support**: Update the IDE detection logic in `kettle_daemon.py`

## License

This project is open source. Feel free to contribute and improve Kettle!