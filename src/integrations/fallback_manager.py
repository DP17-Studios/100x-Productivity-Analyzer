#!/usr/bin/env python3
"""
Fallback Integration Manager - Direct API calls without Composio
Use this if Composio installation fails
"""

import asyncio
import aiohttp
import json
import base64
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

class FallbackManager:
    """Direct API integration manager without Composio dependency"""
    
    def __init__(self, config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self, validate_only=False):
        """Initialize the manager and optionally test connections"""
        self.session = aiohttp.ClientSession()
        
        if not validate_only:
            # Test all connections
            await self._test_github_connection()
            await self._test_jira_connection() 
            await self._test_slack_connection()
            
            logger.info("Fallback integrations initialized successfully")
        else:
            logger.info("Fallback manager session created (validation mode)")
    
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
                elif response.status == 401:
                    error_details = await response.text()
                    raise Exception(
                        f"GitHub API authentication failed (401). "
                        f"Your GITHUB_TOKEN may be invalid, expired, or lack required permissions. "
                        f"Please check your token in the .env file. Details: {error_details}"
                    )
                else:
                    error_details = await response.text()
                    raise Exception(f"GitHub API returned {response.status}: {error_details}")
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
        """Fetch GitHub data with simplified approach"""
        logger.info(f"Fetching GitHub data from {start_date} to {end_date}")
        
        # Format dates for GitHub API
        start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # For organizations, we need to search across repos
        if self.config.organization:
            repos = await self._get_org_repos()
            
            all_prs = []
            all_commits = []
            all_issues = []
            
            for repo in repos[:5]:  # Limit to first 5 repos to avoid rate limits
                repo_name = repo['name']
                
                # Fetch PRs for this repo
                prs = await self._fetch_repo_pulls(repo_name, start_str, end_str)
                all_prs.extend(prs)
                
                # Fetch commits for this repo
                commits = await self._fetch_repo_commits(repo_name, start_str, end_str)
                all_commits.extend(commits)
                
                # Fetch issues for this repo
                issues = await self._fetch_repo_issues(repo_name, start_str, end_str)
                all_issues.extend(issues)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.5)
            
            # Fetch reviews for all PRs
            reviews = await self._fetch_pr_reviews(all_prs)
            
            return GitHubData(
                pull_requests=all_prs,
                commits=all_commits,
                reviews=reviews,
                issues=all_issues
            )
        else:
            # No organization specified, return empty data
            logger.warning("No GitHub organization specified")
            return GitHubData([], [], [], [])
    
    async def _get_org_repos(self) -> List[Dict[str, Any]]:
        """Get repositories for the organization"""
        repos = []
        page = 1
        
        while page <= 3:  # Limit to 3 pages
            url = f'https://api.github.com/orgs/{self.config.organization}/repos'
            params = {
                'type': 'all',
                'sort': 'updated',
                'page': page,
                'per_page': 30
            }
            
            async with self.session.get(
                url,
                headers=self.config.github_headers,
                params=params
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch repos: {response.status}")
                    break
                
                data = await response.json()
                if not data:
                    break
                
                repos.extend(data)
                page += 1
        
        logger.info(f"Found {len(repos)} repositories")
        return repos
    
    async def _fetch_repo_pulls(self, repo_name: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch pull requests for a specific repo"""
        pulls = []
        
        url = f'https://api.github.com/repos/{self.config.organization}/{repo_name}/pulls'
        params = {
            'state': 'all',
            'sort': 'updated',
            'direction': 'desc',
            'per_page': 50
        }
        
        async with self.session.get(
            url,
            headers=self.config.github_headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                # Filter by date range
                filtered_pulls = [
                    pr for pr in data
                    if start_date <= pr['updated_at'] <= end_date
                ]
                pulls.extend(filtered_pulls)
        
        return pulls
    
    async def _fetch_repo_commits(self, repo_name: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch commits for a specific repo"""
        commits = []
        
        url = f'https://api.github.com/repos/{self.config.organization}/{repo_name}/commits'
        params = {
            'since': start_date,
            'until': end_date,
            'per_page': 50
        }
        
        async with self.session.get(
            url,
            headers=self.config.github_headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                commits.extend(data)
        
        return commits
    
    async def _fetch_repo_issues(self, repo_name: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch issues for a specific repo"""
        issues = []
        
        url = f'https://api.github.com/repos/{self.config.organization}/{repo_name}/issues'
        params = {
            'state': 'all',
            'sort': 'updated',
            'since': start_date,
            'per_page': 50
        }
        
        async with self.session.get(
            url,
            headers=self.config.github_headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                # Filter out pull requests (GitHub treats PRs as issues)
                filtered_issues = [
                    issue for issue in data
                    if 'pull_request' not in issue and
                    start_date <= issue['updated_at'] <= end_date
                ]
                issues.extend(filtered_issues)
        
        return issues
    
    async def _fetch_pr_reviews(self, pull_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch reviews for pull requests"""
        reviews = []
        
        for pr in pull_requests[:10]:  # Limit to avoid rate limits
            repo_name = pr['base']['repo']['name']
            pr_number = pr['number']
            
            url = f'https://api.github.com/repos/{self.config.organization}/{repo_name}/pulls/{pr_number}/reviews'
            
            async with self.session.get(
                url,
                headers=self.config.github_headers
            ) as response:
                if response.status == 200:
                    pr_reviews = await response.json()
                    reviews.extend(pr_reviews)
            
            await asyncio.sleep(0.1)  # Rate limiting
        
        return reviews
    
    async def fetch_jira_data(self, start_date: datetime, end_date: datetime) -> JiraData:
        """Fetch Jira data"""
        logger.info(f"Fetching Jira data from {start_date} to {end_date}")
        
        if not self.config.jira_project_key:
            logger.warning("No Jira project key specified")
            return JiraData([], [], [])
        
        # Format dates for Jira JQL
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch tickets
        tickets = await self._fetch_jira_tickets(start_str, end_str)
        
        # Fetch comments (simplified)
        comments = []
        
        # Extract transitions from changelogs
        transitions = self._extract_jira_transitions(tickets)
        
        return JiraData(
            tickets=tickets,
            comments=comments,
            transitions=transitions
        )
    
    async def _fetch_jira_tickets(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch Jira tickets with simplified JQL"""
        tickets = []
        
        auth = aiohttp.BasicAuth(self.config.jira_email, self.config.jira_api_token)
        jql = f"project = {self.config.jira_project_key} AND updated >= '{start_date}' AND updated <= '{end_date}'"
        
        url = f'{self.config.jira_url}/rest/api/2/search'
        params = {
            'jql': jql,
            'maxResults': 100,
            'expand': 'changelog'
        }
        
        async with self.session.get(
            url,
            auth=auth,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                tickets = data.get('issues', [])
        
        logger.info(f"Fetched {len(tickets)} Jira tickets")
        return tickets
    
    def _extract_jira_transitions(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract status transitions from ticket changelogs"""
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
                        logger.info("Message posted to Slack successfully")
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