#!/usr/bin/env python3
"""
Simple Productivity Agent - Core functionality only
Use this if the full agent has dependency issues
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, ensure environment variables are set")

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
except ImportError:
    # Fallback to basic print
    class SimpleConsole:
        def print(self, text, style=None):
            # Remove rich markup tags for plain output
            import re
            clean_text = re.sub(r'\[.*?\]', '', str(text))
            print(clean_text)
    console = SimpleConsole()

class SimpleProductivityAgent:
    """Minimal productivity agent with core functionality"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.organization = os.getenv('ORGANIZATION', '')
        self.lookback_days = int(os.getenv('LOOKBACK_DAYS', '7'))
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def run_analysis(self):
        """Run simple productivity analysis"""
        console.print("🚀 Simple Productivity Analysis", style="bold blue")
        console.print(f"Analyzing last {self.lookback_days} days for {self.organization}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        # Get basic GitHub data
        try:
            github_data = self.fetch_github_data(start_date, end_date)
            stats = self.calculate_simple_stats(github_data)
            self.display_results(stats)
            
        except Exception as e:
            console.print(f"Error: {e}", style="red")
    
    def fetch_github_data(self, start_date, end_date):
        """Fetch basic GitHub data"""
        console.print("Fetching GitHub data...")
        
        # Get repositories
        repos_url = f'https://api.github.com/orgs/{self.organization}/repos'
        response = requests.get(repos_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repos: {response.status_code}")
        
        repos = response.json()[:5]  # Limit to first 5 repos
        
        all_prs = []
        all_commits = []
        
        for repo in repos:
            repo_name = repo['name']
            console.print(f"Processing {repo_name}...")
            
            # Get PRs
            prs_url = f'https://api.github.com/repos/{self.organization}/{repo_name}/pulls'
            prs_response = requests.get(prs_url, headers=self.headers, params={'state': 'all', 'per_page': 50})
            
            if prs_response.status_code == 200:
                prs = prs_response.json()
                # Filter by date
                filtered_prs = [
                    pr for pr in prs
                    if start_date.strftime('%Y-%m-%d') <= pr['created_at'][:10] <= end_date.strftime('%Y-%m-%d')
                ]
                all_prs.extend(filtered_prs)
            
            # Get commits
            commits_url = f'https://api.github.com/repos/{self.organization}/{repo_name}/commits'
            commits_response = requests.get(
                commits_url, 
                headers=self.headers, 
                params={
                    'since': start_date.isoformat(),
                    'until': end_date.isoformat(),
                    'per_page': 50
                }
            )
            
            if commits_response.status_code == 200:
                commits = commits_response.json()
                all_commits.extend(commits)
        
        return {
            'pull_requests': all_prs,
            'commits': all_commits
        }
    
    def calculate_simple_stats(self, github_data):
        """Calculate basic statistics"""
        engineer_stats = {}
        
        # Process PRs
        for pr in github_data['pull_requests']:
            author = pr['user']['login']
            if author not in engineer_stats:
                engineer_stats[author] = {'prs': 0, 'commits': 0, 'score': 0}
            engineer_stats[author]['prs'] += 1
        
        # Process commits
        for commit in github_data['commits']:
            author = commit['commit']['author']['name']
            if author not in engineer_stats:
                engineer_stats[author] = {'prs': 0, 'commits': 0, 'score': 0}
            engineer_stats[author]['commits'] += 1
        
        # Calculate simple scores
        for author, stats in engineer_stats.items():
            # Simple scoring: PRs worth 10 points, commits worth 2 points
            stats['score'] = stats['prs'] * 10 + stats['commits'] * 2
        
        # Sort by score
        sorted_engineers = sorted(
            engineer_stats.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        return {
            'engineers': sorted_engineers,
            'total_prs': len(github_data['pull_requests']),
            'total_commits': len(github_data['commits']),
            'total_engineers': len(engineer_stats)
        }
    
    def display_results(self, stats):
        """Display results in console"""
        console.print("\n" + "="*60)
        console.print("📊 PRODUCTIVITY SUMMARY", style="bold")
        console.print("="*60)
        
        # Summary stats
        console.print(f"Total Engineers: {stats['total_engineers']}")
        console.print(f"Total PRs: {stats['total_prs']}")
        console.print(f"Total Commits: {stats['total_commits']}")
        console.print("")
        
        # Top contributors
        console.print("🏆 TOP CONTRIBUTORS:", style="bold")
        console.print("-" * 60)
        
        if hasattr(console, 'print') and hasattr(Table, '__init__'):
            # Rich table if available
            try:
                table = Table()
                table.add_column("Rank", style="cyan")
                table.add_column("Engineer", style="magenta")
                table.add_column("Score", style="green")
                table.add_column("PRs", style="blue")
                table.add_column("Commits", style="yellow")
                
                for i, (engineer, data) in enumerate(stats['engineers'][:10], 1):
                    table.add_row(
                        str(i),
                        engineer,
                        str(data['score']),
                        str(data['prs']),
                        str(data['commits'])
                    )
                
                console.print(table)
            except:
                # Fallback to simple print
                self._print_simple_table(stats)
        else:
            self._print_simple_table(stats)
        
        console.print("\n" + "="*60)
        
        # Show top 3
        top_3 = stats['engineers'][:3]
        if top_3:
            console.print("\n🥇 TOP 3 CONTRIBUTORS:")
            for i, (engineer, data) in enumerate(top_3, 1):
                medal = ["🥇", "🥈", "🥉"][i-1]
                console.print(f"{medal} {engineer} - Score: {data['score']} (PRs: {data['prs']}, Commits: {data['commits']})")
    
    def _print_simple_table(self, stats):
        """Fallback table printing"""
        print(f"{'Rank':<5} {'Engineer':<20} {'Score':<8} {'PRs':<6} {'Commits':<8}")
        print("-" * 50)
        
        for i, (engineer, data) in enumerate(stats['engineers'][:10], 1):
            print(f"{i:<5} {engineer[:20]:<20} {data['score']:<8} {data['prs']:<6} {data['commits']:<8}")

def main():
    """Main entry point"""
    try:
        agent = SimpleProductivityAgent()
        agent.run_analysis()
        
    except KeyboardInterrupt:
        console.print("\nAnalysis stopped by user")
    except Exception as e:
        console.print(f"\nError: {e}", style="red")
        console.print("\nTroubleshooting:")
        console.print("1. Check your .env file has GITHUB_TOKEN and ORGANIZATION set")
        console.print("2. Verify your GitHub token has repo access permissions")
        console.print("3. Ensure the organization name is correct")
        sys.exit(1)

if __name__ == "__main__":
    main()