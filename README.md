# Productivity Agent

A comprehensive Python agent that integrates GitHub, Jira, and Slack to track and analyze team productivity using local LLM capabilities.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy the example environment file and add your API keys:
```bash
copy .env.example .env
```

Edit `.env` and add your:
- **GitHub Personal Access Token** (Go to GitHub Settings > Developer settings > Personal access tokens)
- **Jira URL, email, and API token** (Atlassian Account Settings > Security > API tokens)
- **Slack Bot Token and channel** (Create Slack app at api.slack.com with `chat:write`, `channels:read` scopes)
- **Optional: Composio API key** (Visit app.composio.dev)

### 3. Test Setup
Verify everything is working:
```bash
python test_setup.py
```

### 4. Run Agent
Start the productivity agent:
```bash
python main.py
```

## Installation Options

### Option 1: Automatic Setup (Recommended)

```bash
# Windows
install.bat

# Manual Installation
python setup.py
```

### Option 2: Manual Installation

```bash
# 1. Fix any dependency conflicts
python fix_pydantic.py

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Copy environment file
copy .env.example .env

# 4. Edit .env with your API keys
notepad .env

# 5. Test the installation
python test_agent.py
```

## Troubleshooting Dependencies

### Dependency Version Conflicts
**Symptoms:**
- `llama-index-instrumentation 0.2.0 requires pydantic>=2.11.5`
- `thinc 8.3.6 requires numpy<3.0.0,>=2.0.0`

**Solution:**
```bash
# Update both dependencies to required versions
pip install --upgrade "pydantic>=2.11.5" "numpy>=2.0.0"

# Or use the automated fix script
python fix_pydantic.py

# Then retry installation
pip install -r requirements.txt
```

### Problem: Composio Installation Fails
The agent automatically falls back to direct API calls without Composio.

```bash
# Install just the essential dependencies
pip install python-dotenv requests aiohttp rich numpy pandas scikit-learn
```

### Problem: LlamaIndex Installation Fails
The agent automatically falls back to TF-IDF based semantic analysis.

```bash
# Install minimal ML dependencies
pip install scikit-learn numpy
```

## Compatibility
- Python 3.8+
- Windows, macOS, Linux
- No virtual environment required
- Replit compatible
- All Unicode characters removed for Windows console compatibility

## Features

- **Multi-Platform Integration**: Connects to GitHub, Jira, and Slack via Composio API (with direct API fallback)
- **Semantic Analysis**: TF-IDF based similarity matching (or LlamaIndex with full install)
- **Productivity Scoring**: Context-aware scoring algorithm for engineer contributions
- **Daily Reports**: Automated daily summaries with top contributors
- **ASCII Console Output**: Clean, ASCII-only visual displays compatible with all systems
- **Local Processing**: No external APIs required (OpenAI-free)
- **Replit Compatible**: Designed to work seamlessly in Replit environment
- **Fallback Systems**: Graceful degradation when advanced features unavailable

## Architecture

```
Productivity Agent
├── GitHub Integration     → Pull Requests, Commits, Reviews, Issues (Direct API)
├── Jira Integration      → Tickets, Comments, Status Transitions (Direct API)
├── Slack Integration     → Daily report posting (Direct API)
├── Semantic Indexing     → Local LlamaIndex or TF-IDF fallback
├── Productivity Scoring  → Multi-factor algorithm with normalization
├── Summary Generation    → Executive & detailed reports
└── ASCII Visualization   → Console tables, charts, and rankings
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required |
| `JIRA_URL` | Jira instance URL | Required |
| `JIRA_EMAIL` | Jira user email | Required |
| `JIRA_API_TOKEN` | Jira API token | Required |
| `SLACK_BOT_TOKEN` | Slack bot token | Required |
| `SLACK_CHANNEL` | Target Slack channel | #productivity-reports |
| `ORGANIZATION` | GitHub organization name | Required |
| `JIRA_PROJECT_KEY` | Jira project key | Required |
| `TIMEZONE` | Report timezone | UTC |
| `DAILY_REPORT_TIME` | Daily report time (HH:MM) | 09:00 |
| `LOOKBACK_DAYS` | Analysis period in days | 7 |
| `MAX_CONTRIBUTORS` | Max contributors to analyze | 10 |
| `DEBUG` | Enable debug logging | false |

## API Token Setup

### GitHub Token
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with these scopes:
   - `repo` (Full repository access)
   - `read:user` (Read user profile)
   - `read:org` (Read organization data)

### Jira Token
1. Go to Jira → Account settings → Security → API tokens
2. Create API token
3. Use your email + token for authentication

### Slack Bot Token
1. Go to https://api.slack.com/apps
2. Create new app or use existing
3. Go to OAuth & Permissions
4. Add these scopes:
   - `chat:write` (Post messages)
   - `channels:read` (List channels)
5. Install app to workspace
6. Copy Bot User OAuth Token

## Productivity Scoring Algorithm

The agent uses a multi-factor scoring system:

### GitHub Score (35%)
- Pull Requests created/merged (45%)
- Code reviews performed (25%)
- Commits made (15%)
- Lines of code changed (10%)
- Issues created/resolved (5%)

### Jira Score (30%)
- Tickets completed (40%)
- Story points delivered (25%)
- Velocity (completion ratio) (15%)
- Tickets created (10%)
- Comments and collaboration (10%)

### Collaboration Score (20%)
- Code review participation
- Meaningful comments and feedback
- Cross-team interactions

### Quality Score (15%)
- Detailed PR descriptions
- Comprehensive commit messages
- Documentation quality
- Semantic similarity analysis

## Sample Output

```
================================================================================
+------------------------------------------------------------------------------+
|                         DAILY PRODUCTIVITY REPORT                           |
+------------------------------------------------------------------------------+
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                              Top Contributors                               │
├──────┬────────────────────┬────────┬─────┬─────────┬─────────────────────────┤
│ Rank │       Engineer     │ Score  │ PRs │ Commits │        Tickets          │
├──────┼────────────────────┼────────┼─────┼─────────┼─────────────────────────┤
│  1   │ Alice Developer    │  89.5  │  12 │    45   │           8             │
│  2   │ Bob Coder         │  76.2  │   8 │    32   │           5             │
│  3   │ Charlie Programmer │  71.8  │   6 │    28   │           6             │
└──────┴────────────────────┴────────┴─────┴─────────┴─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Executive Summary                                 │
│                                                                             │
│ • 15/18 engineers active                                                    │
│ • 45 pull requests created                                                  │
│ • 234 commits made                                                          │
│ • 67 tickets completed                                                      │
│ • Average productivity score: 64.3/100                                     │
│                                                                             │
│ Team performance level: HIGH                                                │
│                                                                             │
│ Top performing areas: GitHub Activity, Code Quality                        │
│ Areas for improvement: Jira Delivery, Collaboration                        │
└─────────────────────────────────────────────────────────────────────────────┘

================================================================================
```

## Running the Agent

### Quick Test Run
```bash
# Run once with current configuration
python main.py --run-now
```

### Continuous Operation
```bash
# Run continuously with daily scheduling
python main.py
```

### Simple Version (Minimal Dependencies)
```bash
# If full installation fails
python simple_agent.py
```

## Project Structure

```
productivity-agent/
├── main.py                 # Main entry point
├── run_agent.py           # Alternative runner
├── simple_agent.py        # Minimal version
├── test_agent.py          # Test suite
├── requirements.txt       # Dependencies
├── .env.example          # Environment template
├── README.md             # This file
├── src/
│   ├── config.py         # Configuration management
│   ├── integrations/
│   │   └── composio_manager.py  # API integrations
│   ├── semantic/
│   │   └── indexer.py    # LlamaIndex semantic analysis
│   ├── analytics/
│   │   └── productivity_scorer.py  # Scoring algorithm
│   ├── reports/
│   │   └── summary_generator.py    # Report generation
│   └── utils/
│       ├── logger.py     # Logging configuration
│       └── ascii_art.py  # ASCII visualization
├── data/                 # Local data storage
├── logs/                 # Application logs
└── requirements_*.txt    # Alternative dependency files
```

## Common Issues and Solutions

### "Required environment variable X is not set"
- Ensure `.env` file exists and contains all required variables
- Check that variable names match exactly (case-sensitive)

### "GitHub connection failed"
- Verify GitHub token has correct permissions
- Check if token is expired
- Ensure organization name is correct

### "Jira connection failed"
- Verify Jira URL format (include https://)
- Check email and API token combination
- Ensure user has project access

### "Slack posting failed"
- Verify bot token starts with `xoxb-`
- Check bot has permission to post in target channel
- Ensure channel name includes `#` prefix

### Memory Errors During Semantic Indexing
**Solution:**
```bash
# Use minimal indexer or reduce data processing:
LOOKBACK_DAYS=1
MAX_CONTRIBUTORS=5
```

### Slow Performance
**Optimizations:**
1. Reduce `LOOKBACK_DAYS` in .env
2. Limit `MAX_CONTRIBUTORS`
3. Use minimal dependencies
4. Run analysis less frequently

## Debug Mode

Enable debug logging:
```env
DEBUG=true
```

Check logs in `logs/` directory for detailed information.

## Minimal Working Configuration

If all else fails, this minimal setup will work:

```bash
# Install only essentials
pip install python-dotenv requests rich

# Create minimal .env
echo GITHUB_TOKEN=your_token > .env
echo ORGANIZATION=your_org >> .env
echo DEBUG=true >> .env

# Run with fallbacks
python main.py --run-now
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests: `python test_agent.py`
5. Submit pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review logs for error details
3. Enable debug mode: `DEBUG=true` in .env
4. Run individual component tests:
   ```bash
   python -c "from src.config import Config; print('Config OK')"
   python -c "from src.utils.ascii_art import ASCIIRenderer; print('ASCII OK')"
   ```

For specific issues, run the agent with debug mode and check the detailed logs in the `logs/` directory.