#!/usr/bin/env python3
"""
Summary Generator - Creates daily productivity summaries and reports
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
import json
import statistics

# Local imports
from ..analytics.productivity_scorer import ProductivityScore
from ..integrations.composio_manager import GitHubData, JiraData

logger = logging.getLogger(__name__)

@dataclass
class TeamSummary:
    """Summary statistics for the team"""
    total_engineers: int
    active_engineers: int
    total_prs: int
    total_commits: int
    total_tickets: int
    average_score: float
    productivity_trend: str
    top_areas: List[str]
    improvement_areas: List[str]

class SummaryGenerator:
    """Generates comprehensive productivity summaries and reports"""
    
    def __init__(self, config):
        self.config = config
        
        # Templates for different summary types
        self.templates = {
            'executive': self._get_executive_template(),
            'detailed': self._get_detailed_template(),
            'slack': self._get_slack_template()
        }
    
    async def generate_summary(
        self,
        scores: List[ProductivityScore],
        github_data: GitHubData,
        jira_data: JiraData
    ) -> Dict[str, Any]:
        """Generate comprehensive summary of productivity data"""
        logger.info("Generating productivity summary")
        
        # Calculate team statistics
        team_stats = self._calculate_team_stats(scores, github_data, jira_data)
        
        # Generate different summary types
        summary = {
            'timestamp': datetime.now().isoformat(),
            'period': f"{self.config.lookback_days} days",
            'team_stats': team_stats,
            'top_performers': scores[:5],
            'executive_summary': self._generate_executive_summary(team_stats, scores),
            'detailed_analysis': self._generate_detailed_analysis(team_stats, scores),
            'trends': self._analyze_trends(scores, github_data, jira_data),
            'recommendations': self._generate_recommendations(team_stats, scores)
        }
        
        return summary
    
    def _calculate_team_stats(self, scores: List[ProductivityScore], github_data: GitHubData, jira_data: JiraData) -> TeamSummary:
        """Calculate team-level statistics"""
        if not scores:
            return TeamSummary(
                total_engineers=0,
                active_engineers=0,
                total_prs=0,
                total_commits=0,
                total_tickets=0,
                average_score=0.0,
                productivity_trend="stable",
                top_areas=[],
                improvement_areas=[]
            )
        
        # Basic counts
        total_engineers = len(scores)
        active_engineers = len([s for s in scores if s.total_score > 10])
        
        # GitHub totals
        total_prs = sum(s.github_stats.prs_created for s in scores)
        total_commits = sum(s.github_stats.commits_made for s in scores)
        
        # Jira totals
        total_tickets = sum(s.jira_stats.tickets_completed for s in scores)
        
        # Average score
        average_score = statistics.mean(s.total_score for s in scores)
        
        # Determine productivity trend
        high_performers = len([s for s in scores if s.total_score > 70])
        if high_performers / total_engineers > 0.3:
            productivity_trend = "high"
        elif high_performers / total_engineers > 0.1:
            productivity_trend = "moderate"
        else:
            productivity_trend = "low"
        
        # Identify top performing areas
        avg_github = statistics.mean(s.github_score for s in scores)
        avg_jira = statistics.mean(s.jira_score for s in scores)
        avg_collab = statistics.mean(s.collaboration_score for s in scores)
        avg_quality = statistics.mean(s.quality_score for s in scores)
        
        area_scores = [
            ("GitHub Activity", avg_github),
            ("Jira Delivery", avg_jira),
            ("Collaboration", avg_collab),
            ("Code Quality", avg_quality)
        ]
        
        area_scores.sort(key=lambda x: x[1], reverse=True)
        top_areas = [area[0] for area in area_scores[:2]]
        improvement_areas = [area[0] for area in area_scores[-2:]]
        
        return TeamSummary(
            total_engineers=total_engineers,
            active_engineers=active_engineers,
            total_prs=total_prs,
            total_commits=total_commits,
            total_tickets=total_tickets,
            average_score=average_score,
            productivity_trend=productivity_trend,
            top_areas=top_areas,
            improvement_areas=improvement_areas
        )
    
    def _generate_executive_summary(self, team_stats: TeamSummary, scores: List[ProductivityScore]) -> str:
        """Generate executive-level summary"""
        if not scores:
            return "No productivity data available for the analysis period."
        
        top_performer = scores[0] if scores else None
        
        summary_parts = [
            f"Team Productivity Analysis ({self.config.lookback_days}-day period):",
            f"",
            f"• {team_stats.active_engineers}/{team_stats.total_engineers} engineers active",
            f"• {team_stats.total_prs} pull requests created",
            f"• {team_stats.total_commits} commits made", 
            f"• {team_stats.total_tickets} tickets completed",
            f"• Average productivity score: {team_stats.average_score:.1f}/100",
            f"",
            f"Team performance level: {team_stats.productivity_trend.upper()}",
            f"",
            f"Top performing areas: {', '.join(team_stats.top_areas)}",
            f"Areas for improvement: {', '.join(team_stats.improvement_areas)}"
        ]
        
        if top_performer:
            summary_parts.extend([
                f"",
                f"Top contributor: {top_performer.engineer} (Score: {top_performer.total_score:.1f})"
            ])
        
        return "\n".join(summary_parts)
    
    def _generate_detailed_analysis(self, team_stats: TeamSummary, scores: List[ProductivityScore]) -> Dict[str, Any]:
        """Generate detailed analysis breakdown"""
        if not scores:
            return {}
        
        # Score distribution
        score_ranges = {
            "high (70-100)": len([s for s in scores if s.total_score >= 70]),
            "medium (40-69)": len([s for s in scores if 40 <= s.total_score < 70]),
            "low (0-39)": len([s for s in scores if s.total_score < 40])
        }
        
        # Component analysis
        component_averages = {
            "github_score": statistics.mean(s.github_score for s in scores),
            "jira_score": statistics.mean(s.jira_score for s in scores),
            "collaboration_score": statistics.mean(s.collaboration_score for s in scores),
            "quality_score": statistics.mean(s.quality_score for s in scores)
        }
        
        # Activity patterns
        activity_patterns = {
            "pr_creators": len([s for s in scores if s.github_stats.prs_created > 0]),
            "active_reviewers": len([s for s in scores if s.github_stats.prs_reviewed > 2]),
            "ticket_completers": len([s for s in scores if s.jira_stats.tickets_completed > 0]),
            "high_collaborators": len([s for s in scores if s.collaboration_score > 60])
        }
        
        return {
            "score_distribution": score_ranges,
            "component_averages": component_averages,
            "activity_patterns": activity_patterns,
            "team_size": len(scores),
            "analysis_period": f"{self.config.lookback_days} days"
        }
    
    def _analyze_trends(self, scores: List[ProductivityScore], github_data: GitHubData, jira_data: JiraData) -> Dict[str, Any]:
        """Analyze productivity trends and patterns"""
        trends = {
            "overall_health": "stable",
            "github_activity": "moderate",
            "jira_delivery": "moderate",
            "collaboration_level": "moderate",
            "key_insights": []
        }
        
        if not scores:
            return trends
        
        # Analyze overall health
        avg_score = statistics.mean(s.total_score for s in scores)
        if avg_score > 70:
            trends["overall_health"] = "excellent"
        elif avg_score > 50:
            trends["overall_health"] = "good"
        elif avg_score > 30:
            trends["overall_health"] = "fair"
        else:
            trends["overall_health"] = "needs_attention"
        
        # Analyze GitHub activity
        total_github_activity = sum(
            s.github_stats.prs_created + s.github_stats.commits_made + s.github_stats.prs_reviewed
            for s in scores
        )
        
        if total_github_activity > len(scores) * 10:  # More than 10 activities per person
            trends["github_activity"] = "high"
        elif total_github_activity > len(scores) * 5:  # More than 5 activities per person
            trends["github_activity"] = "moderate"
        else:
            trends["github_activity"] = "low"
        
        # Analyze Jira delivery
        total_tickets_completed = sum(s.jira_stats.tickets_completed for s in scores)
        if total_tickets_completed > len(scores) * 3:  # More than 3 tickets per person
            trends["jira_delivery"] = "high"
        elif total_tickets_completed > len(scores) * 1.5:  # More than 1.5 tickets per person
            trends["jira_delivery"] = "moderate"
        else:
            trends["jira_delivery"] = "low"
        
        # Analyze collaboration
        avg_collab = statistics.mean(s.collaboration_score for s in scores)
        if avg_collab > 60:
            trends["collaboration_level"] = "high"
        elif avg_collab > 40:
            trends["collaboration_level"] = "moderate"
        else:
            trends["collaboration_level"] = "low"
        
        # Generate insights
        insights = []
        
        high_performers = [s for s in scores if s.total_score > 70]
        if len(high_performers) > len(scores) * 0.3:
            insights.append("Strong team performance with multiple high contributors")
        
        if trends["github_activity"] == "high":
            insights.append("High GitHub activity indicates active development")
        
        if trends["jira_delivery"] == "high":
            insights.append("Excellent ticket completion rate")
        
        if trends["collaboration_level"] == "low":
            insights.append("Consider increasing code review and collaboration activities")
        
        quality_scores = [s.quality_score for s in scores]
        if statistics.mean(quality_scores) > 70:
            insights.append("High code quality standards maintained")
        
        trends["key_insights"] = insights
        
        return trends
    
    def _generate_recommendations(self, team_stats: TeamSummary, scores: List[ProductivityScore]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not scores:
            return ["Insufficient data for recommendations"]
        
        # Overall team performance recommendations
        if team_stats.average_score < 40:
            recommendations.append(
                "Team productivity is below average. Consider reviewing current processes and providing additional support."
            )
        
        # GitHub activity recommendations
        avg_github = statistics.mean(s.github_score for s in scores)
        if avg_github < 40:
            recommendations.append(
                "GitHub activity is low. Encourage more frequent commits, PR creation, and code reviews."
            )
        
        # Jira delivery recommendations
        avg_jira = statistics.mean(s.jira_score for s in scores)
        if avg_jira < 40:
            recommendations.append(
                "Jira delivery metrics are low. Review sprint planning and ticket estimation processes."
            )
        
        # Collaboration recommendations
        avg_collab = statistics.mean(s.collaboration_score for s in scores)
        if avg_collab < 40:
            recommendations.append(
                "Team collaboration is below optimal. Encourage more peer reviews and knowledge sharing."
            )
        
        # Quality recommendations
        avg_quality = statistics.mean(s.quality_score for s in scores)
        if avg_quality < 50:
            recommendations.append(
                "Code quality metrics suggest room for improvement. Consider implementing coding standards and documentation practices."
            )
        
        # Individual performance recommendations
        low_performers = [s for s in scores if s.total_score < 30]
        if len(low_performers) > 0:
            recommendations.append(
                f"{len(low_performers)} engineer(s) may benefit from additional mentoring and support."
            )
        
        # Positive reinforcement
        high_performers = [s for s in scores if s.total_score > 70]
        if len(high_performers) > 0:
            recommendations.append(
                f"Recognize and celebrate {len(high_performers)} top performer(s) for their excellent contributions."
            )
        
        return recommendations
    
    def format_slack_message(self, top_contributors: List[ProductivityScore], summary: Dict[str, Any]) -> str:
        """Format message for Slack posting"""
        team_stats = summary.get('team_stats')
        
        if not team_stats or not top_contributors:
            return "No productivity data available for today's report."
        
        # Header
        message_parts = [
            ":rocket: *Daily Productivity Report* :rocket:",
            f"*Period:* {summary['period']}",
            ""
        ]
        
        # Team overview
        message_parts.extend([
            ":bar_chart: *Team Overview*",
            f"• Active Engineers: {team_stats.active_engineers}/{team_stats.total_engineers}",
            f"• Pull Requests: {team_stats.total_prs}",
            f"• Commits: {team_stats.total_commits}",
            f"• Tickets Completed: {team_stats.total_tickets}",
            f"• Average Score: {team_stats.average_score:.1f}/100",
            ""
        ])
        
        # Top contributors
        message_parts.append(":star: *Top Contributors*")
        for i, contributor in enumerate(top_contributors[:3], 1):
            medal = [":first_place_medal:", ":second_place_medal:", ":third_place_medal:"][i-1]
            message_parts.append(
                f"{medal} {contributor.engineer} - Score: {contributor.total_score:.1f} "
                f"(PRs: {contributor.github_stats.prs_created}, "
                f"Tickets: {contributor.jira_stats.tickets_completed})"
            )
        
        message_parts.append("")
        
        # Key insights
        trends = summary.get('trends', {})
        insights = trends.get('key_insights', [])
        if insights:
            message_parts.append(":bulb: *Key Insights*")
            for insight in insights[:2]:  # Limit to top 2 insights for Slack
                message_parts.append(f"• {insight}")
            message_parts.append("")
        
        # Call to action
        message_parts.append(":point_right: Keep up the great work, team!")
        
        return "\n".join(message_parts)
    
    def _get_executive_template(self) -> str:
        """Get template for executive summary"""
        return """
Team Productivity Summary - {period}

KEY METRICS:
• Active Engineers: {active_engineers}/{total_engineers}
• Total Deliverables: {total_prs} PRs, {total_commits} commits, {total_tickets} tickets
• Average Productivity Score: {average_score:.1f}/100
• Performance Level: {productivity_trend}

TOP AREAS: {top_areas}
IMPROVEMENT AREAS: {improvement_areas}

TOP PERFORMER: {top_performer}
"""
    
    def _get_detailed_template(self) -> str:
        """Get template for detailed analysis"""
        return """
Detailed Productivity Analysis

SCORE DISTRIBUTION:
• High Performance (70-100): {high_count}
• Medium Performance (40-69): {medium_count} 
• Low Performance (0-39): {low_count}

COMPONENT AVERAGES:
• GitHub Activity: {github_avg:.1f}
• Jira Delivery: {jira_avg:.1f}
• Collaboration: {collab_avg:.1f}
• Code Quality: {quality_avg:.1f}

ACTIVITY PATTERNS:
• PR Creators: {pr_creators}
• Active Reviewers: {reviewers}
• Ticket Completers: {completers}
• High Collaborators: {collaborators}
"""
    
    def _get_slack_template(self) -> str:
        """Get template for Slack messages"""
        return """
:rocket: *Daily Productivity Report* :rocket:

:bar_chart: *Team Overview*
• Active: {active_engineers}/{total_engineers} engineers
• Delivered: {total_prs} PRs, {total_tickets} tickets
• Avg Score: {average_score:.1f}/100

:star: *Top Contributors*
{top_contributors}

:bulb: *Insights*
{insights}
"""
    
    async def save_summary(self, summary: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save summary to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"productivity_summary_{timestamp}.json"
        
        filepath = os.path.join(self.config.data_dir, filename)
        
        # Convert ProductivityScore objects to dicts for JSON serialization
        serializable_summary = self._make_json_serializable(summary)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_summary, f, indent=2, default=str)
            
            logger.info(f"Summary saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            raise
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, ProductivityScore):
            return {
                'engineer': obj.engineer,
                'github_stats': obj.github_stats.__dict__,
                'jira_stats': obj.jira_stats.__dict__,
                'github_score': obj.github_score,
                'jira_score': obj.jira_score,
                'collaboration_score': obj.collaboration_score,
                'quality_score': obj.quality_score,
                'velocity_score': obj.velocity_score,
                'total_score': obj.total_score,
                'percentile_rank': obj.percentile_rank
            }
        elif isinstance(obj, TeamSummary):
            return obj.__dict__
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        else:
            return obj