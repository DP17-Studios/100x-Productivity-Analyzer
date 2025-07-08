#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Productivity Agent - GitHub/Jira/Slack Integration

A comprehensive agent that:
- Integrates with GitHub, Jira, and Slack via Composio
- Uses TF-IDF based semantic indexing of PR descriptions, commits, and Jira tickets
- Generates daily productivity summaries with context-aware scoring
- Posts top contributors to Slack and displays ASCII output to console
- Uses only local processing and no external APIs
"""

import os
import sys
import asyncio
import argparse
import schedule
from datetime import datetime, timedelta

# Set UTF-8 encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except AttributeError:
        pass
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

import time
import pytz
from dotenv import load_dotenv
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.config import Config
from src.analytics.productivity_scorer import ProductivityScorer, ProductivityScore
from src.reports.summary_generator import SummaryGenerator
from src.utils.logger import setup_logger
from src.utils.ascii_art import ASCIIRenderer

# Using TF-IDF based semantic indexer
from src.semantic.indexer import SimpleSemanticIndexer as SemanticIndexer

# Composio integration
from src.integrations.composio_manager import ComposioManager, GitHubData, JiraData

# Load environment variables
load_dotenv()

# Setup console and logging
console = Console()
logger = setup_logger(__name__)

class ProductivityAgent:
    """Main agent class that orchestrates all components"""
    
    def __init__(self):
        self.config = Config()
        self.composio_manager = None
        self.semantic_indexer = None
        self.productivity_scorer = None
        self.summary_generator = None
        self.ascii_renderer = None
        self.is_running = False
        self.last_run = None
        console.print("[blue]Productivity Agent initialized[/blue]")
        
    async def initialize(self, validate_only=False):
        """Initialize all components and validate configuration"""
        try:
            # Initialize core components
            self.composio_manager = ComposioManager(self.config)
            self.semantic_indexer = SemanticIndexer(self.config)
            self.productivity_scorer = ProductivityScorer(self.config)
            self.summary_generator = SummaryGenerator(self.config)
            self.ascii_renderer = ASCIIRenderer()
            
            # Initialize integrations  
            await self.composio_manager.initialize(validate_only=validate_only)
            await self.semantic_indexer.initialize()
            console.print("[green]All integrations initialized[/green]")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            console.print(f"[red]Initialization failed: {e}[/red]")
            return False
    
    async def run_productivity_analysis(self, start_date=None, end_date=None):
        """Run comprehensive productivity analysis"""
        try:
            self.is_running = True
            console.print("[yellow]Starting productivity analysis...[/yellow]")
            
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now(pytz.timezone(self.config.timezone))
            if not start_date:
                start_date = end_date - timedelta(days=self.config.lookback_days)
            
            console.print(f"[blue]Analyzing data from {start_date.date()} to {end_date.date()}[/blue]")
            
            # Step 1: Collect data from all sources
            console.print("[cyan]Collecting GitHub data...[/cyan]")
            github_data = await self.composio_manager.fetch_github_data(start_date, end_date)
            
            console.print("[cyan]Collecting Jira data...[/cyan]")
            jira_data = await self.composio_manager.fetch_jira_data(start_date, end_date)
            
            # Step 2: Index content for semantic analysis
            console.print("[cyan]Performing semantic analysis...[/cyan]")
            await self.semantic_indexer.index_data(github_data, jira_data)
            
            # Step 3: Calculate productivity scores
            console.print("[cyan]Calculating productivity scores...[/cyan]")
            scores = await self.productivity_scorer.calculate_scores(github_data, jira_data, start_date, end_date)
            
            # Step 4: Generate summary and insights
            console.print("[cyan]Generating executive summary...[/cyan]")
            summary = await self.summary_generator.generate_summary(
                scores, github_data, jira_data
            )
            
            # Step 5: Display results
            self.display_results(scores, summary)
            
            # Step 6: Post to Slack if configured
            if hasattr(self.config, 'slack_bot_token') and self.config.slack_bot_token:
                console.print("[cyan]Posting results to Slack...[/cyan]")
                await self.post_results_to_slack(scores, summary)
            
            self.last_run = datetime.now()
            self.is_running = False
            
            console.print("[bold green]Analysis completed successfully![/bold green]")
            
            # Return analysis results
            return {
                'timestamp': datetime.now().isoformat(),
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'scores': self._serialize_scores(scores),
                'summary': self._serialize_summary(summary),
                'github_data': {
                    'total_prs': len(github_data.pull_requests),
                    'total_commits': len(github_data.commits),
                    'total_reviews': len(github_data.reviews)
                },
                'jira_data': {
                    'total_issues': len(jira_data.tickets),
                    'completed_issues': len([t for t in jira_data.tickets if t.get('status', '').lower() == 'done'])
                }
            }
            
        except Exception as e:
            self.is_running = False
            logger.error(f"Analysis failed: {e}")
            console.print(f"[red]Analysis failed: {e}[/red]")
            raise
    
    def _serialize_scores(self, scores):
        """Convert ProductivityScore objects to serializable format"""
        scores_data = []
        for score in scores:
            scores_data.append({
                'engineer': score.engineer,
                'total_score': round(score.total_score, 2),
                'github_score': round(score.github_score, 2),
                'jira_score': round(score.jira_score, 2),
                'quality_score': round(score.quality_score, 2),
                'collaboration_score': round(score.collaboration_score, 2),
                'percentile_rank': round(score.percentile_rank, 2),
                'github_stats': {
                    'prs_created': score.github_stats.prs_created,
                    'prs_reviewed': score.github_stats.prs_reviewed,
                    'commits_made': score.github_stats.commits_made,
                    'lines_added': score.github_stats.lines_added,
                    'lines_removed': score.github_stats.lines_deleted
                },
                'jira_stats': {
                    'tickets_completed': score.jira_stats.tickets_completed,
                    'tickets_in_progress': score.jira_stats.tickets_in_progress,
                    'story_points': score.jira_stats.story_points_completed,
                    'avg_completion_time': score.jira_stats.time_to_completion
                }
            })
        return scores_data
    
    def _serialize_summary(self, summary):
        """Convert summary with TeamSummary objects to serializable format"""
        if not summary:
            return {}
            
        serialized = {}
        for key, value in summary.items():
            if key == 'team_stats' and hasattr(value, '__dict__'):
                # Convert TeamSummary object to dictionary
                serialized[key] = {
                    'total_engineers': value.total_engineers,
                    'active_engineers': value.active_engineers,
                    'total_prs': value.total_prs,
                    'total_commits': value.total_commits,
                    'total_tickets': value.total_tickets,
                    'average_score': value.average_score,
                    'productivity_trend': value.productivity_trend,
                    'top_areas': value.top_areas,
                    'improvement_areas': value.improvement_areas
                }
            elif key == 'top_performers':
                # Handle list of ProductivityScore objects
                serialized[key] = self._serialize_scores(value)
            else:
                serialized[key] = value
                
        return serialized
    
    def display_results(self, scores, summary):
        """Display results in console with ASCII art"""
        console.print("\n" + "="*80)
        console.print("[bold blue]PRODUCTIVITY ANALYSIS RESULTS[/bold blue]")
        console.print("="*80)
        
        if not scores:
            console.print("[yellow]No productivity data found for the specified period.[/yellow]")
            return
        
        # Display statistics summary
        console.print(f"\n[bold cyan]Analysis Summary[/bold cyan]")
        console.print(f"Engineers analyzed: {len(scores)}")
        console.print(f"Average team score: {sum(s.total_score for s in scores) / len(scores):.1f}")
        console.print(f"Top performer: {scores[0].engineer} ({scores[0].total_score:.1f})")
        
        # Display top contributors table
        table = Table(title="Top Contributors", show_header=True, header_style="bold magenta")
        table.add_column("Rank", justify="center", style="cyan", width=6)
        table.add_column("Engineer", justify="left", style="green", width=20)
        table.add_column("Score", justify="right", style="yellow", width=8)
        table.add_column("GitHub", justify="center", style="blue", width=8)
        table.add_column("Jira", justify="center", style="red", width=8)
        table.add_column("Quality", justify="center", style="magenta", width=8)
        table.add_column("Collab", justify="center", style="cyan", width=8)
        
        for i, score in enumerate(scores[:self.config.max_contributors]):
            rank_emoji = ["#1", "#2", "#3"][i] if i < 3 else f"#{i+1}"
            table.add_row(
                rank_emoji,
                score.engineer,
                f"{score.total_score:.1f}",
                f"{score.github_score:.1f}",
                f"{score.jira_score:.1f}",
                f"{score.quality_score:.1f}",
                f"{score.collaboration_score:.1f}"
            )
        
        console.print("")
        console.print(table)
        
        # Display executive summary
        if summary and summary.get('executive_summary'):
            console.print("\n[bold green]Executive Summary[/bold green]")
            console.print(Panel(summary['executive_summary'], border_style="green", padding=(1, 2)))
        
        # Display ASCII art for top performer
        if scores:
            top_performer = scores[0]
            ascii_art = self.ascii_renderer.create_banner(f"CHAMPION: {top_performer.engineer}", '*', 80)
            console.print(f"\n[bold yellow]{ascii_art}[/bold yellow]")
        
        console.print("\n" + "="*80)
        
    async def post_results_to_slack(self, scores, summary):
        """Post results to Slack channel"""
        try:
            if not scores:
                return
            
            top_3 = scores[:3]
            message = f"Daily Productivity Report ({datetime.now().strftime('%Y-%m-%d')})\n\n"
            
            for i, score in enumerate(top_3):
                emoji = ["#1", "#2", "#3"][i]
                message += f"{emoji} {score.engineer} - Score: {score.total_score:.1f}\n"
            
            if summary and summary.get('executive_summary'):
                message += f"\nSummary: {summary['executive_summary'][:200]}..."
            
            await self.composio_manager.post_to_slack(message)
            console.print("[green]Results posted to Slack successfully[/green]")
            
        except Exception as e:
            logger.error(f"Failed to post to Slack: {e}")
            console.print(f"[red]Failed to post to Slack: {e}[/red]")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.composio_manager:
            await self.composio_manager.cleanup()
        console.print("[blue]Agent cleanup completed[/blue]")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Productivity Agent - Console & Scheduled Modes')
    parser.add_argument('--mode', choices=['console', 'scheduled'], 
                       default='console', help='Run mode')
    parser.add_argument('--schedule-time', default='09:00', 
                       help='Daily schedule time (HH:MM)')
    
    args = parser.parse_args()
    
    # Display banner
    console.print("\n[bold blue]Productivity Agent v3.0[/bold blue]")
    console.print("[dim]GitHub, Jira & Slack Integration with TF-IDF Analytics[/dim]\n")
    
    if args.mode == 'console':
        # Run single analysis in console mode
        async def run_console():
            agent = ProductivityAgent()
            if await agent.initialize():
                await agent.run_productivity_analysis()
            await agent.cleanup()
        
        console.print("[green]Running productivity analysis...[/green]")
        asyncio.run(run_console())
        
    elif args.mode == 'scheduled':
        # Run scheduled analysis
        async def run_scheduled():
            agent = ProductivityAgent()
            if await agent.initialize():
                await agent.run_productivity_analysis()
                await agent.cleanup()
        
        def scheduled_job():
            console.print(f"[yellow]Running scheduled analysis at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_scheduled())
            loop.close()
        
        schedule.every().day.at(args.schedule_time).do(scheduled_job)
        
        console.print(f"[green]Productivity Agent scheduled to run daily at {args.schedule_time}[/green]")
        console.print(f"[yellow]Next run: {args.schedule_time} (press Ctrl+C to stop)[/yellow]")

        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            console.print("\n[yellow]Scheduler stopped gracefully[/yellow]")

if __name__ == '__main__':
    main()