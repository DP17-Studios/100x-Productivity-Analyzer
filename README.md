# 100x Productivity Agent

A comprehensive productivity monitoring and analysis system that integrates with GitHub, Jira, and Slack to provide insights into your development workflow.

## Features

### Core Analytics
- **Productivity Scoring**: Advanced metrics calculating productivity scores based on:
  - Code commits and changes
  - Issue resolution patterns
  - Communication effectiveness
  - Work pattern analysis
- **Semantic Analysis**: TF-IDF-based text analysis for understanding content relationships
- **Time Tracking**: Automated tracking of development activities
- **Goal Setting & Progress**: Set and monitor productivity goals

### Integrations
- **GitHub Integration**: Track commits, pull requests, and repository activity
- **Jira Integration**: Monitor issue resolution, sprint progress, and project management
- **Slack Integration**: Analyze communication patterns and collaboration metrics

### Advanced Features
- **ASCII Art Rendering**: Beautiful terminal output with enhanced visuals
- **Data Persistence**: Local storage with JSON and pickle-based caching
- **Configurable Analytics**: Customizable scoring algorithms and metrics
- **Real-time Monitoring**: Live updates and notifications

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DP17-Studios/100x-Engineer-Analyzer
   cd 100x
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with your API credentials:
   ```
   GITHUB_TOKEN=your_github_token
   JIRA_TOKEN=your_jira_token
   SLACK_TOKEN=your_slack_token
   COMPOSIO_API_KEY=your_composio_api_key
   ```

## Usage

### Basic Usage

Run the main productivity agent:
```bash
python main.py
```

### Configuration

The system uses several configuration files:
- `config/settings.json` - Main application settings
- `config/integrations.json` - Integration-specific configurations
- `config/analytics.json` - Analytics and scoring parameters

### Project Structure

```
100x/
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── config/                     # Configuration files
│   ├── settings.json
│   ├── integrations.json
│   └── analytics.json
├── src/
│   ├── analytics/              # Productivity analytics and scoring
│   │   └── productivity_scorer.py
│   ├── integrations/           # External service integrations
│   │   └── composio_manager.py
│   ├── semantic/               # Text analysis and semantic processing
│   │   └── indexer.py
│   └── utils/                  # Utility functions and helpers
│       ├── ascii_art.py
│       ├── config_manager.py
│       ├── data_manager.py
│       ├── goal_tracking.py
│       └── time_tracker.py
└── data/                       # Data storage and cache
    ├── cache/
    └── logs/
```

## Key Components

### Productivity Scorer
The `ProductivityScorer` class provides comprehensive analysis:
- Code quality metrics
- Commit frequency and patterns
- Issue resolution efficiency
- Communication effectiveness scores

### Composio Manager
Handles all external integrations:
- GitHub repository analysis
- Jira project tracking
- Slack workspace monitoring
- Unified data collection and processing

### Semantic Indexer
TF-IDF based semantic analysis:
- Content similarity detection
- Topic modeling and clustering
- Automated tagging and categorization
- Search and retrieval capabilities

### Data Management
- Persistent storage with automatic backups
- Efficient caching mechanisms
- Data export and reporting features
- Privacy-focused local storage

## Advanced Configuration

### Analytics Customization
Modify `config/analytics.json` to adjust:
- Scoring algorithm weights
- Productivity thresholds
- Report generation settings
- Goal tracking parameters

### Integration Settings
Configure `config/integrations.json` for:
- API rate limiting
- Data synchronization intervals
- Service-specific preferences
- Authentication methods

## Development

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings for all functions and classes
- Include error handling and logging

## Troubleshooting

### Common Issues
1. **API Authentication Errors**: Verify your tokens in the `.env` file
2. **Missing Dependencies**: Run `pip install -r requirements.txt`
3. **Data Loading Issues**: Check file permissions in the `data/` directory
4. **Integration Failures**: Verify network connectivity and API status

### Logging
Logs are stored in `data/logs/` with different levels:
- `debug.log` - Detailed debugging information
- `info.log` - General application events
- `error.log` - Error messages and exceptions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions, please:
1. Check existing issues in the repository
2. Create a new issue with detailed information
3. Follow the contribution guidelines

---

**Note**: This is a productivity monitoring tool designed to help developers track and improve their workflow efficiency. All data processing is performed locally to ensure privacy and security.
