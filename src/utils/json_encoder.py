#!/usr/bin/env python3
"""
Custom JSON encoder for serializing application-specific objects
"""

import json
from datetime import datetime, date
from ..analytics.productivity_scorer import ProductivityScore, GitHubStats, JiraStats

class EngineerAnalyzerJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles serialization of application-specific objects
    such as ProductivityScore, GitHubStats, and JiraStats.
    """
    
    def default(self, obj):
        # Handle ProductivityScore objects
        if isinstance(obj, ProductivityScore):
            return {
                'engineer': obj.engineer,
                'total_score': round(obj.total_score, 2),
                'github_score': round(obj.github_score, 2),
                'jira_score': round(obj.jira_score, 2),
                'quality_score': round(obj.quality_score, 2),
                'collaboration_score': round(obj.collaboration_score, 2),
                'velocity_score': round(obj.velocity_score, 2),
                'percentile_rank': round(obj.percentile_rank, 2),
                'github_stats': obj.github_stats,
                'jira_stats': obj.jira_stats
            }
        
        # Handle GitHubStats objects
        elif isinstance(obj, GitHubStats):
            return {
                'prs_created': obj.prs_created,
                'prs_merged': obj.prs_merged,
                'prs_reviewed': obj.prs_reviewed,
                'commits_made': obj.commits_made,
                'lines_added': obj.lines_added,
                'lines_deleted': obj.lines_deleted,
                'files_changed': obj.files_changed,
                'issues_created': obj.issues_created,
                'issues_closed': obj.issues_closed,
                'review_comments': obj.review_comments
            }
        
        # Handle JiraStats objects
        elif isinstance(obj, JiraStats):
            return {
                'tickets_created': obj.tickets_created,
                'tickets_completed': obj.tickets_completed,
                'tickets_in_progress': obj.tickets_in_progress,
                'story_points_completed': obj.story_points_completed,
                'comments_made': obj.comments_made,
                'time_in_review': obj.time_in_review,
                'time_to_completion': obj.time_to_completion
            }
        
        # Handle datetime and date objects
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Let the base class handle other types or raise TypeError
        return super().default(obj)