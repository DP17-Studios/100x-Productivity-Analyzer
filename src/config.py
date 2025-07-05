#!/usr/bin/env python3
"""
Configuration management for the Productivity Agent
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Central configuration class for all agent settings"""
    
    # API Keys
    github_token: str
    jira_url: str
    jira_email: str
    jira_api_token: str
    slack_bot_token: str
    slack_channel: str
    
    # Organization settings
    organization: str
    jira_project_key: str
    
    # Agent settings
    timezone: str
    daily_report_time: str
    lookback_days: int
    max_contributors: int
    debug: bool
    
    # Local paths
    data_dir: str
    embeddings_dir: str
    logs_dir: str
    
    def __init__(self):
        # Composio API key (optional - fallback to direct APIs if not available)
        self.composio_api_key = os.getenv('COMPOSIO_API_KEY')
        
        # API Keys - Load from environment, validate later
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.jira_url = os.getenv('JIRA_URL', '')
        self.jira_email = os.getenv('JIRA_EMAIL', '')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN', '')
        self.slack_bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        
        # Optional settings with defaults
        slack_channel_raw = os.getenv('SLACK_CHANNEL', 'productivity-reports')
        # Ensure channel name starts with # for Slack API
        self.slack_channel = slack_channel_raw if slack_channel_raw.startswith('#') else f'#{slack_channel_raw}'
        self.organization = os.getenv('GITHUB_ORG', '')
        self.jira_project_key = os.getenv('JIRA_PROJECT_KEY', '')
        self.timezone = os.getenv('TIMEZONE', 'UTC')
        self.daily_report_time = os.getenv('DAILY_REPORT_TIME', '09:00')
        self.lookback_days = int(os.getenv('LOOKBACK_DAYS', '7'))
        self.max_contributors = int(os.getenv('MAX_CONTRIBUTORS', '10'))
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Local directories
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, 'data')
        self.embeddings_dir = os.path.join(self.data_dir, 'embeddings')
        self.logs_dir = os.path.join(base_dir, 'logs')
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.embeddings_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable {key} is not set. "
                f"Please check your .env file."
            )
        return value
    
    @property
    def github_headers(self) -> dict:
        """GitHub API headers"""
        return {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ProductivityAgent/1.0'
        }
    
    @property
    def jira_auth(self) -> tuple:
        """Jira authentication tuple"""
        return (self.jira_email, self.jira_api_token)
    
    @property
    def slack_headers(self) -> dict:
        """Slack API headers"""
        return {
            'Authorization': f'Bearer {self.slack_bot_token}',
            'Content-Type': 'application/json'
        }
    
    def validate(self) -> bool:
        """Validate all configuration settings"""
        try:
            # Check required fields
            required_fields = [
                'github_token', 'jira_url', 'jira_email', 
                'jira_api_token', 'slack_bot_token'
            ]
            
            for field in required_fields:
                if not getattr(self, field):
                    raise ValueError(f"Required field {field} is empty")
            
            # Validate URLs
            if not self.jira_url.startswith(('http://', 'https://')):
                raise ValueError("JIRA_URL must be a valid URL")
            
            # Validate numeric values
            if self.lookback_days <= 0:
                raise ValueError("LOOKBACK_DAYS must be positive")
            
            if self.max_contributors <= 0:
                raise ValueError("MAX_CONTRIBUTORS must be positive")
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation (hiding sensitive data)"""
        return f"""Config(
    organization={self.organization}
    jira_project_key={self.jira_project_key}
    timezone={self.timezone}
    daily_report_time={self.daily_report_time}
    lookback_days={self.lookback_days}
    max_contributors={self.max_contributors}
    debug={self.debug}
    data_dir={self.data_dir}
)"""