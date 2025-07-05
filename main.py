#!/usr/bin/env python3
"""
Productivity Agent - GitHub/Jira/Slack Integration

A comprehensive agent that:
- Integrates with GitHub, Jira, and Slack via Composio
- Uses LlamaIndex for semantic indexing of PR descriptions, commits, and Jira tickets
- Generates daily productivity summaries with context-aware scoring
- Posts top contributors to Slack and displays ASCII output to console
- Uses only local LLMs and no external APIs
"""

import os
import sys
import asyncio
import schedule
import time
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.config import Config
from src.analytics.productivity_scorer import ProductivityScorer
from src.reports.summary_generator import SummaryGenerator
from src.utils.logger import setup_logger
from src.utils.ascii_art import ASCIIRenderer

# Try to import LlamaIndex indexer, fall back to simple version if not available
try:
    from src.semantic.indexer import SemanticIndexer
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    from src.semantic.simple_indexer import SimpleSemanticIndexer as SemanticIndexer
    LLAMAINDEX_AVAILABLE = False

# Default to direct API integration, Composio optional
try:
    from src.integrations.composio_manager import ComposioManager
    COMPOSIO_AVAILABLE = True
except ImportError:
    from src.integrations.fallback_manager import FallbackManager as ComposioManager
    COMPOSIO_AVAILABLE = False

# Load environment variables
load_dotenv()

# Setup console and logging
console = Console()
logger = setup_logger(__name__)

class ProductivityAgent:
    """Main agent class that orchestrates all components"""
    
    def __init__(self):
        self.config = Config()
        self.composio_manager = None  # Initialize after validation
        self.semantic_indexer = None  # Initialize after validation
        self.productivity_scorer = None  # Initialize after validation
        self.summary_generator = None  # Initialize after validation
        self.ascii_renderer = ASCIIRenderer()
        
    async def initialize(self):
        """Initialize all components"""
        try:
            console.print("[bold blue]Initializing Productivity Agent...[/bold blue]")
            
            if not COMPOSIO_AVAILABLE:
                console.print("[blue]Using direct API integration (Composio optional)[/blue]")
            
            # Validate configuration before initializing
            console.print("[cyan]Validating configuration...[/cyan]")
            validation_result = self._validate_configuration()
            if not validation_result['valid']:
                console.print(f"[red]Configuration Error: {validation_result['message']}[/red]")
                console.print("[yellow]Please check your .env file and ensure all required API keys are configured.[/yellow]")
                return False
            
            console.print("[green]Configuration validation passed![/green]")
            
            # Create components after validation passes
            self.composio_manager = ComposioManager(self.config)
            self.semantic_indexer = SemanticIndexer(self.config)
            self.productivity_scorer = ProductivityScorer(self.config)
            self.summary_generator = SummaryGenerator(self.config)
            
            # Initialize API connections
            await self.composio_manager.initialize(validate_only=False)
            if COMPOSIO_AVAILABLE:
                console.print("[green]Composio integrations initialized[/green]")
            else:
                console.print("[green]Direct API integrations initialized[/green]")
            
            # Initialize semantic indexer
            await self.semantic_indexer.initialize()
            if LLAMAINDEX_AVAILABLE:
                console.print("[green]LlamaIndex semantic indexer initialized[/green]")
            else:
                console.print("[green]Simple TF-IDF semantic indexer initialized[/green]")
            
            console.print("[bold green]Agent initialization complete![/bold green]")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            console.print(f"[bold red]Initialization failed: {e}[/bold red]")
            
            # Provide specific guidance for common issues
            error_str = str(e).lower()
            if "401" in error_str and "github" in error_str:
                console.print("\n[yellow]GitHub Token Issue Detected:[/yellow]")
                console.print("1. Your GitHub token may be expired or invalid")
                console.print("2. Generate a new token at: https://github.com/settings/tokens")  
                console.print("3. Token needs 'repo', 'read:user', and 'read:org' permissions")
                console.print("4. Update GITHUB_TOKEN in your .env file")
            
            raise
    
    def _validate_configuration(self):
        """Validate that required API keys are configured"""
        required_keys = {
            'GITHUB_TOKEN': 'GitHub API token is required for accessing repository data',
            'GITHUB_ORG': 'GitHub organization name is required',
            'JIRA_URL': 'Jira URL is required for accessing Jira data',
            'JIRA_EMAIL': 'Jira email is required for authentication',
            'JIRA_API_TOKEN': 'Jira API token is required for authentication',
            'SLACK_BOT_TOKEN': 'Slack bot token is required for posting summaries'
        }
        
        missing_keys = []
        placeholder_keys = []
        
        for key, description in required_keys.items():
            value = os.getenv(key)
            if not value:
                missing_keys.append(f"{key} ({description})")
            elif 'your_' in value.lower() or 'token_here' in value.lower() or 'example' in value.lower():
                placeholder_keys.append(f"{key} (appears to be a placeholder value)")
        
        if missing_keys:
            return {
                'valid': False,
                'message': f"Missing required environment variables: {', '.join(missing_keys)}"
            }
        
        if placeholder_keys:
            return {
                'valid': False,
                'message': f"Please update placeholder values: {', '.join(placeholder_keys)}"
            }
        
        return {'valid': True, 'message': 'Configuration is valid'}
    
    async def run_daily_analysis(self):
        """Run the daily productivity analysis"""
        try:
            console.print("\n[bold yellow]Starting Daily Productivity Analysis...[/bold yellow]")
            
            # Calculate date range
            end_date = datetime.now(pytz.timezone(self.config.timezone))
            start_date = end_date - timedelta(days=self.config.lookback_days)
            
            console.print(f"[cyan]📅 Analyzing period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}[/cyan]")
            
            # Collect data from all sources
            github_data = await self.composio_manager.fetch_github_data(start_date, end_date)
            jira_data = await self.composio_manager.fetch_jira_data(start_date, end_date)
            
            # Index the data semantically
            await self.semantic_indexer.index_data(github_data, jira_data)
            
            # Calculate productivity scores
            scores = await self.productivity_scorer.calculate_scores(
                github_data, jira_data, start_date, end_date
            )
            
            # Generate and display summary
            summary = await self.summary_generator.generate_summary(
                scores, github_data, jira_data
            )
            
            # Display ASCII output
            self.display_console_output(scores, summary)
            
            # Post to Slack
            await self.post_to_slack(scores[:3], summary)
            
            console.print("[bold green]Daily analysis complete![/bold green]")
            
        except Exception as e:
            logger.error(f"Daily analysis failed: {e}")
            console.print(f"[bold red]Daily analysis failed: {e}[/bold red]")
    
    def display_console_output(self, scores, summary):
        """Display results in ASCII format to console"""
        console.print("\n" + "="*80)
        console.print(self.ascii_renderer.create_title("DAILY PRODUCTIVITY REPORT"))
        console.print("="*80)
        
        # Top contributors table
        table = Table(title="Top Contributors")
        table.add_column("Rank", style="cyan", no_wrap=True)
        table.add_column("Engineer", style="magenta")
        table.add_column("Score", style="green")
        table.add_column("PRs", style="blue")
        table.add_column("Commits", style="yellow")
        table.add_column("Tickets", style="red")
        
        for i, score_data in enumerate(scores[:10], 1):
            table.add_row(
                str(i),
                score_data['engineer'],
                f"{score_data['total_score']:.2f}",
                str(score_data['github_stats']['prs_created']),
                str(score_data['github_stats']['commits_made']),
                str(score_data['jira_stats']['tickets_completed'])
            )
        
        console.print(table)
        
        # Summary panel
        summary_panel = Panel(
            summary['overview'],
            title="Executive Summary",
            border_style="blue"
        )
        console.print(summary_panel)
        
        console.print("\n" + "="*80)
    
    async def post_to_slack(self, top_contributors, summary):
        """Post top 3 contributors to Slack"""
        try:
            message = self.summary_generator.format_slack_message(top_contributors, summary)
            await self.composio_manager.post_to_slack(message)
            console.print("[green]Posted summary to Slack[/green]")
        except Exception as e:
            logger.error(f"Failed to post to Slack: {e}")
            console.print(f"[red]Slack posting failed: {e}[/red]")
    
    def schedule_daily_run(self):
        """Schedule the daily analysis"""
        schedule.every().day.at(self.config.daily_report_time).do(
            lambda: asyncio.create_task(self.run_daily_analysis())
        )
        
        console.print(f"[green]⏰ Scheduled daily reports at {self.config.daily_report_time}[/green]")
    
    async def run_forever(self):
        """Run the agent continuously"""
        console.print("[bold green]🔄 Agent running continuously...[/bold green]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

async def main():
    """Main entry point"""
    console.print("[bold blue]Productivity Agent v2.0 - Unified Requirements[/bold blue]\n")
    
    # Show feature availability
    if COMPOSIO_AVAILABLE:
        console.print("[green]Composio integration available[/green]")
    else:
        console.print("[yellow]Composio not available - using direct APIs[/yellow]")
    
    if LLAMAINDEX_AVAILABLE:
        console.print("[green]LlamaIndex semantic analysis available[/green]")
    else:
        console.print("[yellow]LlamaIndex not available - using TF-IDF fallback[/yellow]")
    
    console.print()
    
    try:
        agent = ProductivityAgent()
        initialization_success = await agent.initialize()
        
        if not initialization_success:
            console.print("\n[bold yellow]Setup Instructions:[/bold yellow]")
            console.print("1. Copy .env.example to .env: [blue]copy .env.example .env[/blue]")
            console.print("2. Edit .env file with your actual API keys")
            console.print("3. Run the agent again: [blue]python main.py[/blue]")
            console.print("\n[cyan]For detailed setup instructions, see QUICKSTART.md[/cyan]")
            sys.exit(1)
        
        # Check if we should run immediately or just schedule
        if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
            await agent.run_daily_analysis()
        else:
            agent.schedule_daily_run()
            await agent.run_forever()
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Agent stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Agent crashed: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())