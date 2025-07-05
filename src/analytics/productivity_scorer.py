#!/usr/bin/env python3
"""
Productivity Scorer - Context-aware scoring system for engineer contributions
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging
import math
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Local imports
from ..integrations.composio_manager import GitHubData, JiraData
from ..semantic.indexer import SimpleSemanticIndexer

logger = logging.getLogger(__name__)

@dataclass
class GitHubStats:
    """GitHub statistics for an engineer"""
    prs_created: int = 0
    prs_merged: int = 0
    prs_reviewed: int = 0
    commits_made: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    files_changed: int = 0
    issues_created: int = 0
    issues_closed: int = 0
    review_comments: int = 0
    
@dataclass
class JiraStats:
    """Jira statistics for an engineer"""
    tickets_created: int = 0
    tickets_completed: int = 0
    tickets_in_progress: int = 0
    story_points_completed: int = 0
    comments_made: int = 0
    time_in_review: float = 0.0  # hours
    time_to_completion: float = 0.0  # hours
    
@dataclass
class ProductivityScore:
    """Complete productivity score for an engineer"""
    engineer: str
    github_stats: GitHubStats
    jira_stats: JiraStats
    github_score: float = 0.0
    jira_score: float = 0.0
    collaboration_score: float = 0.0
    quality_score: float = 0.0
    velocity_score: float = 0.0
    total_score: float = 0.0
    percentile_rank: float = 0.0
    
class ProductivityScorer:
    """Calculates context-aware productivity scores for engineers"""
    
    def __init__(self, config):
        self.config = config
        self.semantic_indexer: Optional[SimpleSemanticIndexer] = None
        
        # Scoring weights (can be adjusted)
        self.weights = {
            'github': 0.35,
            'jira': 0.30,
            'collaboration': 0.20,
            'quality': 0.15
        }
        
        # GitHub activity weights
        self.github_weights = {
            'prs_created': 0.20,
            'prs_merged': 0.25,
            'commits_made': 0.15,
            'lines_added': 0.10,
            'prs_reviewed': 0.15,
            'review_comments': 0.10,
            'issues_activity': 0.05
        }
        
        # Jira activity weights
        self.jira_weights = {
            'tickets_completed': 0.40,
            'story_points': 0.25,
            'tickets_created': 0.10,
            'comments_made': 0.10,
            'velocity': 0.15
        }
    
    def set_semantic_indexer(self, indexer: SimpleSemanticIndexer):
        """Set the semantic indexer for quality analysis"""
        self.semantic_indexer = indexer
    
    async def calculate_scores(
        self, 
        github_data: GitHubData, 
        jira_data: JiraData,
        start_date: datetime,
        end_date: datetime
    ) -> List[ProductivityScore]:
        """Calculate productivity scores for all engineers"""
        logger.info("Calculating productivity scores")
        
        # Extract engineer activities
        engineer_activities = self._extract_engineer_activities(
            github_data, jira_data, start_date, end_date
        )
        
        # Calculate raw scores for each engineer
        raw_scores = []
        for engineer, activities in engineer_activities.items():
            score = await self._calculate_engineer_score(engineer, activities)
            raw_scores.append(score)
        
        # Normalize scores and calculate percentiles
        normalized_scores = self._normalize_scores(raw_scores)
        
        # Sort by total score (descending)
        normalized_scores.sort(key=lambda x: x.total_score, reverse=True)
        
        logger.info(f"Calculated scores for {len(normalized_scores)} engineers")
        return normalized_scores
    
    def _extract_engineer_activities(
        self, 
        github_data: GitHubData, 
        jira_data: JiraData,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Extract activities per engineer from GitHub and Jira data"""
        activities = defaultdict(lambda: {
            'github': {
                'prs': [],
                'commits': [],
                'reviews': [],
                'issues': []
            },
            'jira': {
                'tickets': [],
                'comments': [],
                'transitions': []
            }
        })
        
        # Process GitHub data
        for pr in github_data.pull_requests:
            if pr.get('user', {}).get('login'):
                author = pr['user']['login']
                activities[author]['github']['prs'].append(pr)
        
        for commit in github_data.commits:
            commit_data = commit.get('commit', {})
            author_info = commit_data.get('author', {})
            if author_info.get('name'):
                # Try to match commit author with GitHub user
                author = author_info['name']
                activities[author]['github']['commits'].append(commit)
        
        for review in github_data.reviews:
            if review.get('user', {}).get('login'):
                reviewer = review['user']['login']
                activities[reviewer]['github']['reviews'].append(review)
        
        for issue in github_data.issues:
            if issue.get('user', {}).get('login'):
                author = issue['user']['login']
                activities[author]['github']['issues'].append(issue)
        
        # Process Jira data
        for ticket in jira_data.tickets:
            fields = ticket.get('fields', {})
            
            # Assignee
            assignee = fields.get('assignee')
            if assignee and assignee.get('displayName'):
                engineer = assignee['displayName']
                activities[engineer]['jira']['tickets'].append(ticket)
            
            # Creator
            creator = fields.get('creator')
            if creator and creator.get('displayName'):
                engineer = creator['displayName']
                if ticket not in activities[engineer]['jira']['tickets']:
                    activities[engineer]['jira']['tickets'].append(ticket)
        
        for comment in jira_data.comments:
            author = comment.get('author', {})
            if author.get('displayName'):
                engineer = author['displayName']
                activities[engineer]['jira']['comments'].append(comment)
        
        for transition in jira_data.transitions:
            if transition.get('author'):
                engineer = transition['author']
                activities[engineer]['jira']['transitions'].append(transition)
        
        return dict(activities)
    
    async def _calculate_engineer_score(self, engineer: str, activities: Dict[str, Any]) -> ProductivityScore:
        """Calculate productivity score for a single engineer"""
        # Calculate GitHub stats
        github_stats = self._calculate_github_stats(activities['github'])
        
        # Calculate Jira stats
        jira_stats = self._calculate_jira_stats(activities['jira'])
        
        # Calculate component scores
        github_score = self._calculate_github_score(github_stats)
        jira_score = self._calculate_jira_score(jira_stats)
        collaboration_score = await self._calculate_collaboration_score(engineer, activities)
        quality_score = await self._calculate_quality_score(engineer, activities)
        
        # Calculate velocity score
        velocity_score = self._calculate_velocity_score(github_stats, jira_stats)
        
        # Calculate total weighted score
        total_score = (
            github_score * self.weights['github'] +
            jira_score * self.weights['jira'] +
            collaboration_score * self.weights['collaboration'] +
            quality_score * self.weights['quality']
        )
        
        return ProductivityScore(
            engineer=engineer,
            github_stats=github_stats,
            jira_stats=jira_stats,
            github_score=github_score,
            jira_score=jira_score,
            collaboration_score=collaboration_score,
            quality_score=quality_score,
            velocity_score=velocity_score,
            total_score=total_score
        )
    
    def _calculate_github_stats(self, github_activities: Dict[str, List]) -> GitHubStats:
        """Calculate GitHub statistics"""
        stats = GitHubStats()
        
        # PR statistics
        prs = github_activities.get('prs', [])
        stats.prs_created = len(prs)
        stats.prs_merged = len([pr for pr in prs if pr.get('merged_at')])
        
        # Calculate lines changed
        for pr in prs:
            stats.lines_added += pr.get('additions', 0)
            stats.lines_deleted += pr.get('deletions', 0)
            stats.files_changed += pr.get('changed_files', 0)
        
        # Commit statistics
        commits = github_activities.get('commits', [])
        stats.commits_made = len(commits)
        
        # Review statistics
        reviews = github_activities.get('reviews', [])
        stats.prs_reviewed = len(set(review.get('pull_request_url', '') for review in reviews))
        stats.review_comments = len([r for r in reviews if r.get('body')])
        
        # Issue statistics
        issues = github_activities.get('issues', [])
        stats.issues_created = len(issues)
        stats.issues_closed = len([issue for issue in issues if issue.get('state') == 'closed'])
        
        return stats
    
    def _calculate_jira_stats(self, jira_activities: Dict[str, List]) -> JiraStats:
        """Calculate Jira statistics"""
        stats = JiraStats()
        
        tickets = jira_activities.get('tickets', [])
        comments = jira_activities.get('comments', [])
        
        # Ticket statistics
        for ticket in tickets:
            fields = ticket.get('fields', {})
            status = fields.get('status', {}).get('name', '').lower()
            
            if status in ['done', 'closed', 'resolved']:
                stats.tickets_completed += 1
            elif status in ['in progress', 'in development']:
                stats.tickets_in_progress += 1
            
            # Story points
            story_points = fields.get('storyPointEstimate') or fields.get('customfield_10016')
            if story_points and status in ['done', 'closed', 'resolved']:
                stats.story_points_completed += story_points
        
        stats.tickets_created = len(tickets)
        stats.comments_made = len(comments)
        
        return stats
    
    def _calculate_github_score(self, stats: GitHubStats) -> float:
        """Calculate normalized GitHub score (0-100)"""
        # Base scores for different activities
        pr_score = (
            stats.prs_created * self.github_weights['prs_created'] +
            stats.prs_merged * self.github_weights['prs_merged']
        ) * 10
        
        commit_score = stats.commits_made * self.github_weights['commits_made'] * 2
        
        lines_score = min(
            (stats.lines_added + stats.lines_deleted) / 1000 * self.github_weights['lines_added'],
            10  # Cap at 10 points
        ) * 10
        
        review_score = (
            stats.prs_reviewed * self.github_weights['prs_reviewed'] +
            stats.review_comments * self.github_weights['review_comments']
        ) * 5
        
        issues_score = (
            stats.issues_created * 0.5 +
            stats.issues_closed * 1.0
        ) * self.github_weights['issues_activity'] * 10
        
        total = pr_score + commit_score + lines_score + review_score + issues_score
        
        # Apply logarithmic scaling to prevent outliers
        return min(100, math.log10(max(1, total)) * 50)
    
    def _calculate_jira_score(self, stats: JiraStats) -> float:
        """Calculate normalized Jira score (0-100)"""
        completed_score = stats.tickets_completed * self.jira_weights['tickets_completed'] * 15
        
        story_points_score = stats.story_points_completed * self.jira_weights['story_points'] * 5
        
        created_score = stats.tickets_created * self.jira_weights['tickets_created'] * 8
        
        comments_score = stats.comments_made * self.jira_weights['comments_made'] * 3
        
        # Velocity bonus (tickets completed vs created ratio)
        if stats.tickets_created > 0:
            velocity_ratio = stats.tickets_completed / stats.tickets_created
            velocity_bonus = min(velocity_ratio, 2.0) * self.jira_weights['velocity'] * 10
        else:
            velocity_bonus = 0
        
        total = completed_score + story_points_score + created_score + comments_score + velocity_bonus
        
        # Apply logarithmic scaling
        return min(100, math.log10(max(1, total)) * 50)
    
    async def _calculate_collaboration_score(self, engineer: str, activities: Dict[str, Any]) -> float:
        """Calculate collaboration score based on reviews, comments, and interactions"""
        github_activities = activities['github']
        jira_activities = activities['jira']
        
        # GitHub collaboration
        reviews_given = len(github_activities.get('reviews', []))
        review_comments = len([
            r for r in github_activities.get('reviews', []) 
            if r.get('body') and len(r['body'].strip()) > 50
        ])
        
        # Jira collaboration
        jira_comments = len(jira_activities.get('comments', []))
        meaningful_comments = len([
            c for c in jira_activities.get('comments', [])
            if c.get('body') and len(c['body'].strip()) > 100
        ])
        
        # Calculate collaboration score
        github_collab = (reviews_given * 3 + review_comments * 2)
        jira_collab = (jira_comments * 2 + meaningful_comments * 3)
        
        total_collab = github_collab + jira_collab
        
        # Normalize to 0-100
        return min(100, total_collab * 2)
    
    async def _calculate_quality_score(self, engineer: str, activities: Dict[str, Any]) -> float:
        """Calculate quality score using semantic analysis and code metrics"""
        if not self.semantic_indexer:
            return 50.0  # Default score without semantic analysis
        
        quality_indicators = []
        
        # Analyze PR descriptions and commit messages
        github_activities = activities['github']
        
        for pr in github_activities.get('prs', []):
            if pr.get('body') and len(pr['body'].strip()) > 100:
                # Quality indicator: detailed PR descriptions
                quality_indicators.append(min(len(pr['body']) / 500, 2.0))
        
        for commit in github_activities.get('commits', []):
            commit_data = commit.get('commit', {})
            message = commit_data.get('message', '')
            if len(message.strip()) > 50:
                # Quality indicator: detailed commit messages
                quality_indicators.append(min(len(message) / 200, 1.5))
        
        # Analyze Jira ticket descriptions
        jira_activities = activities['jira']
        for ticket in jira_activities.get('tickets', []):
            fields = ticket.get('fields', {})
            description = fields.get('description', '')
            if description and len(description.strip()) > 150:
                # Quality indicator: detailed ticket descriptions
                quality_indicators.append(min(len(description) / 300, 2.0))
        
        # Calculate average quality
        if quality_indicators:
            avg_quality = sum(quality_indicators) / len(quality_indicators)
            return min(100, avg_quality * 30)
        else:
            return 25.0  # Low score for lack of documentation
    
    def _calculate_velocity_score(self, github_stats: GitHubStats, jira_stats: JiraStats) -> float:
        """Calculate velocity score based on completion rates and efficiency"""
        # GitHub velocity indicators
        github_velocity = 0
        if github_stats.prs_created > 0:
            merge_rate = github_stats.prs_merged / github_stats.prs_created
            github_velocity = merge_rate * 50
        
        # Jira velocity indicators
        jira_velocity = 0
        if jira_stats.tickets_created > 0:
            completion_rate = jira_stats.tickets_completed / jira_stats.tickets_created
            jira_velocity = completion_rate * 50
        
        # Story points velocity
        story_points_velocity = min(jira_stats.story_points_completed / 10, 5) * 10
        
        return min(100, github_velocity + jira_velocity + story_points_velocity)
    
    def _normalize_scores(self, scores: List[ProductivityScore]) -> List[ProductivityScore]:
        """Normalize scores and calculate percentile ranks"""
        if not scores:
            return scores
        
        # Extract total scores for normalization
        total_scores = [score.total_score for score in scores]
        
        if len(set(total_scores)) > 1:  # Only normalize if scores vary
            scaler = MinMaxScaler(feature_range=(0, 100))
            normalized_totals = scaler.fit_transform(np.array(total_scores).reshape(-1, 1))
            
            # Update scores with normalized values
            for i, score in enumerate(scores):
                score.total_score = float(normalized_totals[i][0])
        
        # Calculate percentile ranks
        sorted_scores = sorted(total_scores, reverse=True)
        for score in scores:
            rank = sorted_scores.index(score.total_score)
            percentile = ((len(sorted_scores) - rank) / len(sorted_scores)) * 100
            score.percentile_rank = percentile
        
        return scores
    
    def get_scoring_summary(self, scores: List[ProductivityScore]) -> Dict[str, Any]:
        """Get summary statistics about the scoring"""
        if not scores:
            return {}
        
        total_scores = [s.total_score for s in scores]
        github_scores = [s.github_score for s in scores]
        jira_scores = [s.jira_score for s in scores]
        
        return {
            'total_engineers': len(scores),
            'score_stats': {
                'total': {
                    'mean': np.mean(total_scores),
                    'median': np.median(total_scores),
                    'std': np.std(total_scores),
                    'min': np.min(total_scores),
                    'max': np.max(total_scores)
                },
                'github': {
                    'mean': np.mean(github_scores),
                    'median': np.median(github_scores)
                },
                'jira': {
                    'mean': np.mean(jira_scores),
                    'median': np.median(jira_scores)
                }
            },
            'top_performers': [s.engineer for s in scores[:3]],
            'weights_used': self.weights
        }