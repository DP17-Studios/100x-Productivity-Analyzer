# Productivity Agent Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the `.env.template` file to `.env` and fill in your credentials:

```bash
cp .env.template .env
```

Edit the `.env` file with your actual API credentials:

#### Required GitHub Settings:
- **GITHUB_TOKEN**: Personal access token from [GitHub Settings](https://github.com/settings/tokens)
  - Required scopes: `repo`, `read:org`, `read:user`
- **GITHUB_ORG**: Your organization name
- **GITHUB_REPOSITORY**: Repository to analyze (optional)

#### Required Jira Settings:
- **JIRA_URL**: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
- **JIRA_EMAIL**: Your Jira email address
- **JIRA_API_TOKEN**: API token from [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
- **JIRA_PROJECT_KEY**: Your Jira project key

#### Optional Slack Settings:
- **SLACK_BOT_TOKEN**: Bot token from [Slack API](https://api.slack.com/apps)
- **SLACK_CHANNEL**: Channel to post reports (e.g., `#productivity-reports`)

### 3. Run the Analysis
```bash
python main.py
```

## Demo Mode

If you don't have API credentials configured, the application will run in **Demo Mode** with sample data. This allows you to:
- See what the analysis results look like
- Test the functionality before configuring real integrations

## Troubleshooting

### API Connection Issues
1. **Check the console output**: Look for initialization errors
2. **Verify your .env file**: Ensure all required fields are filled
3. **Test with demo mode**: The application should work even without valid credentials

### "Agent not initialized" Error
1. **Check API credentials**: Verify your GitHub and Jira tokens are valid
2. **Check network connectivity**: Ensure you can access GitHub and Jira
3. **Check permissions**: Ensure your tokens have the required scopes
4. **Enable debug mode**: Set `DEBUG=true` in your .env file for detailed logs

### API Rate Limits
- **GitHub**: 5,000 requests/hour for authenticated requests
- **Jira**: Varies by plan, typically 10-20 requests/second
- **Tip**: The agent automatically handles rate limiting and retries

## Advanced Configuration

### Scheduling
Run automated daily reports:
```bash
python main.py --mode scheduled --schedule-time 09:00
```

### Custom Date Range
Analyze specific periods:
```python
# In Python script
await agent.run_productivity_analysis(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

### Configuration Options
- **LOOKBACK_DAYS**: Number of days to analyze (default: 7)
- **MAX_CONTRIBUTORS**: Maximum contributors to show (default: 10)
- **TIMEZONE**: Timezone for analysis (default: UTC)
- **DEBUG**: Enable debug logging (default: false)

## Security Notes

1. **Keep your .env file secure**: Never commit it to version control
2. **Use minimal permissions**: Grant only required scopes to API tokens
3. **Rotate tokens regularly**: Update API tokens periodically
4. **Monitor usage**: Keep track of API usage and rate limits

## Support

- **Check logs**: Look in the `logs/` directory for detailed error information
- **Enable debug mode**: Set `DEBUG=true` for verbose logging
- **Test individual components**: Run the main script to test GitHub/Jira connectivity

## Features


✅ **GitHub Integration** (PRs, commits, reviews)
✅ **Jira Integration** (tickets, story points, completion times)
✅ **Slack Notifications** (optional)
✅ **Productivity Scoring** (with TF-IDF semantic analysis)
✅ **Executive Summaries**
✅ **Team Rankings**
✅ **Historical Data**
✅ **Demo Mode** (works without API credentials)
✅ **Console Interface** (rich text output)

Enjoy analyzing your team's productivity! 🚀
