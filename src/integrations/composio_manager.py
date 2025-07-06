#!/usr/bin/env python3
"""
Composio Manager - GitHub, Jira, and Slack integrations
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GitHubData:
    """GitHub data structure"""
    pull_requests: List[Dict[str, Any]]
    commits: List[Dict[str, Any]]
    reviews: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]

@dataclass
class JiraData:
    """Jira data structure"""
    tickets: List[Dict[str, Any]]
    comments: List[Dict[str, Any]]
    transitions: List[Dict[str, Any]]

class ComposioManager:
    """Manages all API integrations via Composio and direct calls"""
    
    def __init__(self, config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.composio_client = None
        self.composio_available = False
        
    async def initialize(self, validate_only=False):
        """Initialize the manager and test connections"""
        self.session = aiohttp.ClientSession()
        
        # Try to initialize Composio
        await self._initialize_composio()
        
        if self.composio_available:
            logger.info("SUCCESS: Composio integration initialized successfully")
        else:
            logger.warning("WARNING: Composio not available - using direct API calls")
            
        # Test connections
        await self._test_connections()
    
    async def cleanup(self):
        """Clean up resources, especially aiohttp sessions"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Composio manager session closed")
    
    async def _initialize_composio(self):
        """Initialize Composio client"""
        try:
            from composio import ComposioToolSet, App
            
            self.composio_client = ComposioToolSet()
            
            # Test Composio client with different API methods
            try:
                # Try the newer API first
                if hasattr(self.composio_client, 'get_tools'):
                    github_app = self.composio_client.get_tools(apps=[App.GITHUB])
                    jira_app = self.composio_client.get_tools(apps=[App.JIRA])
                    slack_app = self.composio_client.get_tools(apps=[App.SLACK])
                    composio_working = github_app and jira_app and slack_app
                elif hasattr(self.composio_client, 'get_actions'):
                    # Alternative API method
                    actions = self.composio_client.get_actions()
                    composio_working = len(actions) > 0
                else:
                    # Just test if client is functional
                    composio_working = self.composio_client is not None
            except Exception as api_error:
                logger.debug(f"Composio API test failed: {api_error}")
                composio_working = False
            
            if composio_working:
                self.composio_available = True
                logger.info("Composio apps connected: GitHub, Jira, Slack")
            else:
                logger.warning("Some Composio apps not connected - falling back to direct APIs")
                
        except ImportError as e:
            logger.warning(f"Composio not available: {e}")
        except Exception as e:
            logger.error(f"Composio initialization failed: {e}")
            
    async def _test_connections(self):
        """Test all API connections"""
        await self._test_github_connection()
        await self._test_jira_connection()
        await self._test_slack_connection()
        
        logger.info("All integrations initialized successfully")
    
    async def _test_github_connection(self):
        """Test GitHub API connection"""
        try:
            async with self.session.get(
                'https://api.github.com/user',
                headers=self.config.github_headers
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    logger.info(f"GitHub connection successful: {user_data.get('login')}")
                else:
                    raise Exception(f"GitHub API returned {response.status}")
        except Exception as e:
            logger.error(f"GitHub connection failed: {e}")
            raise
    
    async def _test_jira_connection(self):
        """Test Jira API connection"""
        try:
            auth = aiohttp.BasicAuth(self.config.jira_email, self.config.jira_api_token)
            async with self.session.get(
                f'{self.config.jira_url}/rest/api/2/myself',
                auth=auth
            ) as response:
                if response.status == 200:
                    user_data = await response.json()
                    logger.info(f"Jira connection successful: {user_data.get('displayName')}")
                else:
                    raise Exception(f"Jira API returned {response.status}")
        except Exception as e:
            logger.error(f"Jira connection failed: {e}")
            raise
    
    async def _test_slack_connection(self):
        """Test Slack API connection"""
        try:
            async with self.session.post(
                'https://slack.com/api/auth.test',
                headers=self.config.slack_headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        logger.info(f"Slack connection successful: {data.get('user')}")
                    else:
                        raise Exception(f"Slack API error: {data.get('error')}")
                else:
                    raise Exception(f"Slack API returned {response.status}")
        except Exception as e:
            logger.error(f"Slack connection failed: {e}")
            raise
    
    async def fetch_github_data(self, start_date: datetime, end_date: datetime) -> GitHubData:
        """Fetch GitHub data for the specified date range"""
        logger.info(f"Fetching GitHub data from {start_date} to {end_date}")
        
        # Format dates for GitHub API
        start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Fetch PRs
        pull_requests = await self._fetch_github_pulls(start_str, end_str)
        
        # Fetch commits
        commits = await self._fetch_github_commits(start_str, end_str)
        
        # Fetch reviews
        reviews = await self._fetch_github_reviews(pull_requests)
        
        # Fetch issues
        issues = await self._fetch_github_issues(start_str, end_str)
        
        return GitHubData(
            pull_requests=pull_requests,
            commits=commits,
            reviews=reviews,
            issues=issues
        )
    
    async def _fetch_github_pulls(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch pull requests from GitHub"""
        pulls = []
        page = 1
        
        while True:
            url = f'https://api.github.com/repos/{self.config.organization}/{self.config.repository}/pulls'
            params = {
                'state': 'all',
                'sort': 'updated',
                'direction': 'desc',
                'page': page,
                'per_page': 100
            }
            
            async with self.session.get(
                url,
                headers=self.config.github_headers,
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch PRs: {response.status}")
                    break
                
                data = await response.json()
                if not data:
                    break
                
                # Filter by date range
                filtered_pulls = [
                    pr for pr in data
                    if start_date <= pr['updated_at'] <= end_date
                ]
                
                pulls.extend(filtered_pulls)
                
                # Check if we've gone past our date range
                if data and data[-1]['updated_at'] < start_date:
                    break
                
                page += 1
        
        logger.info(f"Fetched {len(pulls)} pull requests")
        return pulls
    
    async def _fetch_github_commits(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch commits from GitHub"""
        commits = []
        page = 1
        
        while True:
            url = f'https://api.github.com/repos/{self.config.organization}/{self.config.repository}/commits'
            params = {
                'since': start_date,
                'until': end_date,
                'page': page,
                'per_page': 100
            }
            
            async with self.session.get(
                url,
                headers=self.config.github_headers,
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch commits: {response.status}")
                    break
                
                data = await response.json()
                if not data:
                    break
                
                commits.extend(data)
                page += 1
        
        logger.info(f"Fetched {len(commits)} commits")
        return commits
    
    async def _fetch_github_reviews(self, pull_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch reviews for pull requests"""
        reviews = []
        
        for pr in pull_requests:
            pr_number = pr['number']
            url = f'https://api.github.com/repos/{self.config.organization}/{self.config.repository}/pulls/{pr_number}/reviews'
            
            async with self.session.get(
                url,
                headers=self.config.github_headers
            ) as response:
                if response.status == 200:
                    pr_reviews = await response.json()
                    reviews.extend(pr_reviews)
                
                # Rate limiting
                await asyncio.sleep(0.1)
        
        logger.info(f"Fetched {len(reviews)} reviews")
        return reviews
    
    async def _fetch_github_issues(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch issues from GitHub"""
        issues = []
        page = 1
        
        while True:
            url = f'https://api.github.com/repos/{self.config.organization}/{self.config.repository}/issues'
            params = {
                'state': 'all',
                'sort': 'updated',
                'direction': 'desc',
                'since': start_date,
                'page': page,
                'per_page': 100
            }
            
            async with self.session.get(
                url,
                headers=self.config.github_headers,
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch issues: {response.status}")
                    break
                
                data = await response.json()
                if not data:
                    break
                
                # Filter out pull requests (GitHub treats PRs as issues)
                filtered_issues = [
                    issue for issue in data
                    if 'pull_request' not in issue and
                    start_date <= issue['updated_at'] <= end_date
                ]
                
                issues.extend(filtered_issues)
                
                # Check if we've gone past our date range
                if data and data[-1]['updated_at'] < start_date:
                    break
                
                page += 1
        
        logger.info(f"Fetched {len(issues)} issues")
        return issues
    
    async def fetch_jira_data(self, start_date: datetime, end_date: datetime) -> JiraData:
        """Fetch Jira data for the specified date range"""
        logger.info(f"Fetching Jira data from {start_date} to {end_date}")
        
        # Format dates for Jira JQL
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch tickets
        tickets = await self._fetch_jira_tickets(start_str, end_str)
        
        # Fetch comments
        comments = await self._fetch_jira_comments(tickets)
        
        # Fetch transitions
        transitions = await self._fetch_jira_transitions(tickets)
        
        return JiraData(
            tickets=tickets,
            comments=comments,
            transitions=transitions
        )
    
    async def _fetch_jira_tickets(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch Jira tickets"""
        tickets = []
        start_at = 0
        max_results = 100
        
        auth = aiohttp.BasicAuth(self.config.jira_email, self.config.jira_api_token)
        
        while True:
            jql = f"project = {self.config.jira_project_key} AND updated >= '{start_date}' AND updated <= '{end_date}'"
            
            url = f'{self.config.jira_url}/rest/api/2/search'
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'expand': 'changelog'
            }
            
            async with self.session.get(
                url,
                auth=auth,
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Jira tickets: {response.status}")
                    break
                
                data = await response.json()
                issues = data.get('issues', [])
                
                if not issues:
                    break
                
                tickets.extend(issues)
                start_at += max_results
                
                # Check if we've reached the end
                if len(issues) < max_results:
                    break
        
        logger.info(f"Fetched {len(tickets)} Jira tickets")
        return tickets
    
    async def _fetch_jira_comments(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch comments for Jira tickets"""
        comments = []
        auth = aiohttp.BasicAuth(self.config.jira_email, self.config.jira_api_token)
        
        for ticket in tickets:
            ticket_key = ticket['key']
            url = f'{self.config.jira_url}/rest/api/2/issue/{ticket_key}/comment'
            
            async with self.session.get(url, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()
                    ticket_comments = data.get('comments', [])
                    comments.extend(ticket_comments)
                
                # Rate limiting
                await asyncio.sleep(0.1)
        
        logger.info(f"Fetched {len(comments)} Jira comments")
        return comments
    
    async def _fetch_jira_transitions(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract transitions from ticket changelogs"""
        transitions = []
        
        for ticket in tickets:
            changelog = ticket.get('changelog', {}).get('histories', [])
            
            for history in changelog:
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        transition = {
                            'ticket_key': ticket['key'],
                            'from_status': item.get('fromString'),
                            'to_status': item.get('toString'),
                            'changed_at': history.get('created'),
                            'author': history.get('author', {}).get('displayName')
                        }
                        transitions.append(transition)
        
        logger.info(f"Extracted {len(transitions)} status transitions")
        return transitions
    
    async def post_to_slack(self, message: str) -> bool:
        """Post message to Slack channel"""
        try:
            payload = {
                'channel': self.config.slack_channel,
                'text': message,
                'as_user': True
            }
            
            async with self.session.post(
                'https://slack.com/api/chat.postMessage',
                headers=self.config.slack_headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        logger.info(f"Message posted to Slack successfully")
                        return True
                    else:
                        logger.error(f"Slack API error: {data.get('error')}")
                        return False
                else:
                    logger.error(f"Failed to post to Slack: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Exception posting to Slack: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()