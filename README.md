# Kettle AI - AI-Powered Project Automation

Kettle is an AI-powered project automation tool that reads Slack messages, extracts coding tasks, and generates/modifies project code using LLMs. It now includes a background daemon that monitors IDE windows and shows a widget when you're coding.

## Features

- **Slack Integration**: Automatically fetches and processes Slack messages
- **Task Extraction**: Uses AI to extract actionable coding tasks from messages
- **Project Matching**: Finds similar existing projects using embeddings
- **Code Generation**: Generates and executes Python scripts for project setup
- **IDE Integration**: Background daemon that shows a widget when IDEs are active
- **Multi-LLM Support**: Works with Anthropic Claude, Google Gemini, and Perplexity AI

## Quick Start

### 1. Setup Configuration

Run the daemon for the first time to configure your IDE paths:

```bash
python kettle_daemon.py
```

This will start an interactive configuration wizard where you can specify:
- Paths to your IDE applications (VSCode, PyCharm, Sublime Text)
- Slack check interval
- Auto-processing settings

### 2. Start the Daemon

```bash
python kettle_daemon.py
```

The daemon will:
- Run continuously in the background
- Monitor for IDE windows (VSCode, PyCharm, etc.)
- Show the Kettle widget when an IDE is active
- Automatically process new Slack messages
- Generate code based on extracted tasks

### 3. Using the Widget

When you open an IDE (like VSCode), a small ☕ widget will appear at the bottom right of your screen. Click it to see:

- Latest Slack message that triggered work
- Extracted tasks with phase indicators
- Generated script status
- Real-time updates

## Manual Pipeline (Alternative)

If you prefer to run the pipeline manually instead of using the daemon:

```bash
python master_pipeline.py
```

This will:
1. Fetch Slack messages
2. Extract tasks
3. Find similar projects
4. Generate and execute code
5. Show the dashboard widget

## Configuration

The daemon uses `kettle_config.json` for configuration:

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
├── master_pipeline.py        # Manual pipeline runner
├── dashboard.py              # Widget UI
├── extract_tasks.py          # Task extraction from messages
├── execute.py                # Code generation and execution
├── project_matcher.py        # Project similarity matching
├── slack_fetch.py            # Slack message fetching
├── prompts.py                # LLM prompts
├── keys.py                   # API keys
├── json/                     # Data storage
│   ├── messages.json         # Slack messages
│   ├── phased_tasks.json     # Extracted tasks
│   ├── project_embeddings.json # Project embeddings
│   └── last_processed_ts.txt # Last processed timestamp
├── gemini/                   # Google Gemini implementation
├── perplexity/               # Perplexity AI implementation
└── kettle_config.json        # Daemon configuration
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

### Widget Not Appearing
- Check that your IDE is in the configuration
- Ensure the daemon is running (`python kettle_daemon.py`)
- Verify IDE paths in `kettle_config.json`

### Slack Messages Not Processing
- Check your Slack API configuration in `keys.py`
- Verify the channel ID in `slack_fetch.py`
- Check the `auto_process_slack` setting in configuration

### Missing Dependencies
```bash
pip install sentence-transformers psutil requests
```

## Development

To modify or extend Kettle:

1. **Add New LLM Provider**: Create a new directory with provider-specific files
2. **Customize Prompts**: Edit `prompts.py` for different task extraction strategies
3. **Extend Widget**: Modify `dashboard.py` for additional UI features
4. **Add IDE Support**: Update the IDE detection logic in `kettle_daemon.py`

## License

This project is open source. Feel free to contribute and improve Kettle!