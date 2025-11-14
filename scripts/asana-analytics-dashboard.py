#!/usr/bin/env python3
"""
Asana Analytics Dashboard

This script generates comprehensive analytics and reports for Asana task completion
metrics, helping you track productivity, identify trends, and optimize workflows.

Usage:
    python asana-analytics-dashboard.py [--days DAYS] [--project PROJECT_ID] [--export FORMAT]

Options:
    --days DAYS         Number of days to analyze (default: 30)
    --project PROJECT   Specific project ID to analyze
    --export FORMAT     Export format: json, csv, html (default: console)
    --team-stats        Include team productivity statistics
    --trend-analysis    Include trend analysis and predictions

Environment Variables:
    ASANA_PAT          Your Asana Personal Access Token
"""

import asana
import os
import sys
import json
import csv
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dateutil.parser import parse
import statistics


class AsanaAnalytics:
    def __init__(self, pat):
        self.client = asana.Client.access_token(pat)
        self.workspace_id = None
        self.user_id = None
        self._initialize()
    
    def _initialize(self):
        """Initialize workspace and user information"""
        try:
            workspaces = list(self.client.workspaces.find_all())
            if workspaces:
                self.workspace_id = workspaces[0]['gid']
                print(f"✅ Connected to workspace: {workspaces[0]['name']}")
            
            me = self.client.users.me()
            self.user_id = me['gid']
            print(f"✅ Authenticated as: {me['name']}")
        except Exception as e:
            print(f"❌ Error initializing: {str(e)}")
            sys.exit(1)
    
    def get_completion_stats(self, days=30, project_id=None):
        """Get task completion statistics for the specified period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"\n📊 Analyzing completion stats from {start_date.date()} to {end_date.date()}")
        
        stats = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'completion_metrics': {},
            'daily_breakdown': {},
            'project_breakdown': {},
            'time_analysis': {},
            'productivity_score': 0
        }
        
        try:
            # Get tasks based on scope
            if project_id:
                tasks = list(self.client.tasks.find_by_project(
                    project_id,
                    {"opt_fields": "name,completed,completed_at,created_at,due_date,assignee.name,projects.name"}
                ))
                project = self.client.projects.find_by_id(project_id, {"opt_fields": "name"})
                print(f"📁 Analyzing project: {project['name']}")
            else:
                tasks = list(self.client.tasks.find_by_user(
                    self.user_id,
                    {
                        "workspace": self.workspace_id,
                        "opt_fields": "name,completed,completed_at,created_at,due_date,assignee.name,projects.name",
                        "completed_since": start_date.isoformat()
                    }
                ))
            
            if not tasks:
                print("ℹ️  No tasks found for the specified criteria")
                return stats
            
            # Analyze tasks
            completed_tasks = []
            incomplete_tasks = []
            overdue_tasks = []
            daily_completions = defaultdict(int)
            project_stats = defaultdict(lambda: {'completed': 0, 'total': 0})
            completion_times = []
            
            for task in tasks:
                # Project breakdown
                for project in task.get('projects', []):
                    project_name = project['name']
                    project_stats[project_name]['total'] += 1
                    
                    if task['completed']:
                        project_stats[project_name]['completed'] += 1
                
                # Completion analysis
                if task['completed'] and task.get('completed_at'):
                    completed_at = parse(task['completed_at'])
                    
                    # Only count completions within our date range
                    if start_date <= completed_at <= end_date:
                        completed_tasks.append(task)
                        
                        # Daily breakdown
                        completion_date = completed_at.date().isoformat()
                        daily_completions[completion_date] += 1
                        
                        # Time to completion analysis
                        if task.get('created_at'):
                            created_at = parse(task['created_at'])
                            completion_time = (completed_at - created_at).total_seconds() / 3600  # hours
                            completion_times.append(completion_time)
                
                elif not task['completed']:
                    incomplete_tasks.append(task)
                    
                    # Check if overdue
                    if task.get('due_date'):
                        due_date = parse(task['due_date'])
                        if due_date.date() < datetime.now().date():
                            overdue_tasks.append(task)
            
            # Calculate metrics
            total_tasks = len(tasks)
            completed_in_period = len(completed_tasks)
            incomplete_count = len(incomplete_tasks)
            overdue_count = len(overdue_tasks)
            
            completion_rate = (completed_in_period / total_tasks * 100) if total_tasks > 0 else 0
            
            stats['completion_metrics'] = {
                'total_tasks': total_tasks,
                'completed_in_period': completed_in_period,
                'incomplete_tasks': incomplete_count,
                'overdue_tasks': overdue_count,
                'completion_rate': round(completion_rate, 2),
                'average_daily_completions': round(completed_in_period / days, 2)
            }
            
            # Daily breakdown
            stats['daily_breakdown'] = dict(daily_completions)
            
            # Project breakdown
            for project_name, project_data in project_stats.items():
                if project_data['total'] > 0:
                    project_completion_rate = (project_data['completed'] / project_data['total']) * 100
                    stats['project_breakdown'][project_name] = {
                        'total_tasks': project_data['total'],
                        'completed_tasks': project_data['completed'],
                        'completion_rate': round(project_completion_rate, 2)
                    }
            
            # Time analysis
            if completion_times:
                stats['time_analysis'] = {
                    'average_completion_time_hours': round(statistics.mean(completion_times), 2),
                    'median_completion_time_hours': round(statistics.median(completion_times), 2),
                    'fastest_completion_hours': round(min(completion_times), 2),
                    'slowest_completion_hours': round(max(completion_times), 2)
                }
            
            # Productivity score (0-100)
            productivity_factors = [
                min(completion_rate, 100),  # Completion rate
                max(0, 100 - (overdue_count / max(total_tasks, 1) * 100)),  # Overdue penalty
                min(100, (completed_in_period / max(days, 1)) * 10)  # Daily completion bonus
            ]
            stats['productivity_score'] = round(statistics.mean(productivity_factors), 2)
            
            return stats
            
        except Exception as e:
            print(f"❌ Error analyzing completion stats: {str(e)}")
            return stats
    
    def get_trend_analysis(self, days=30):
        """Analyze trends over time"""
        print(f"\n📈 Analyzing trends over the last {days} days")
        
        trends = {
            'weekly_trends': [],
            'completion_velocity': 0,
            'predictions': {},
            'recommendations': []
        }
        
        try:
            # Get weekly data for trend analysis
            weeks = days // 7
            for week in range(weeks):
                week_start = datetime.now() - timedelta(days=(week + 1) * 7)
                week_end = week_start + timedelta(days=7)
                
                week_stats = self.get_completion_stats(7, None)
                
                trends['weekly_trends'].append({
                    'week': f"Week {weeks - week}",
                    'start_date': week_start.date().isoformat(),
                    'end_date': week_end.date().isoformat(),
                    'completions': week_stats['completion_metrics']['completed_in_period'],
                    'completion_rate': week_stats['completion_metrics']['completion_rate']
                })
            
            # Calculate velocity (trend direction)
            if len(trends['weekly_trends']) >= 2:
                recent_completions = [w['completions'] for w in trends['weekly_trends'][-3:]]
                if len(recent_completions) >= 2:
                    trends['completion_velocity'] = statistics.mean(recent_completions[-2:]) - statistics.mean(recent_completions[:-1])
            
            # Generate recommendations
            current_stats = self.get_completion_stats(7)
            completion_rate = current_stats['completion_metrics']['completion_rate']
            overdue_rate = (current_stats['completion_metrics']['overdue_tasks'] / 
                          max(current_stats['completion_metrics']['total_tasks'], 1)) * 100
            
            if completion_rate < 50:
                trends['recommendations'].append("🔴 Low completion rate - consider reducing task load or extending deadlines")
            elif completion_rate > 80:
                trends['recommendations'].append("🟢 Excellent completion rate - consider taking on more challenging tasks")
            
            if overdue_rate > 20:
                trends['recommendations'].append("⚠️ High overdue rate - review task priorities and deadlines")
            
            if trends['completion_velocity'] < -1:
                trends['recommendations'].append("📉 Completion rate is declining - investigate potential blockers")
            elif trends['completion_velocity'] > 1:
                trends['recommendations'].append("📈 Completion rate is improving - great momentum!")
            
            return trends
            
        except Exception as e:
            print(f"❌ Error analyzing trends: {str(e)}")
            return trends
    
    def generate_report(self, stats, trends=None, format='console'):
        """Generate formatted report"""
        if format == 'console':
            self._print_console_report(stats, trends)
        elif format == 'json':
            return self._generate_json_report(stats, trends)
        elif format == 'csv':
            return self._generate_csv_report(stats)
        elif format == 'html':
            return self._generate_html_report(stats, trends)
    
    def _print_console_report(self, stats, trends=None):
        """Print formatted console report"""
        print("\n" + "=" * 60)
        print("📊 ASANA PRODUCTIVITY ANALYTICS REPORT")
        print("=" * 60)
        
        # Period info
        period = stats['period']
        print(f"\n📅 Analysis Period: {period['start_date'][:10]} to {period['end_date'][:10]} ({period['days']} days)")
        
        # Completion metrics
        metrics = stats['completion_metrics']
        print(f"\n📈 COMPLETION METRICS")
        print(f"├─ Total Tasks: {metrics['total_tasks']}")
        print(f"├─ Completed in Period: {metrics['completed_in_period']}")
        print(f"├─ Incomplete Tasks: {metrics['incomplete_tasks']}")
        print(f"├─ Overdue Tasks: {metrics['overdue_tasks']}")
        print(f"├─ Completion Rate: {metrics['completion_rate']}%")
        print(f"└─ Avg Daily Completions: {metrics['average_daily_completions']}")
        
        # Productivity score
        score = stats['productivity_score']
        score_emoji = "🔥" if score >= 80 else "✅" if score >= 60 else "⚠️" if score >= 40 else "🔴"
        print(f"\n🎯 PRODUCTIVITY SCORE: {score_emoji} {score}/100")
        
        # Project breakdown
        if stats['project_breakdown']:
            print(f"\n📁 PROJECT BREAKDOWN")
            for project, data in stats['project_breakdown'].items():
                print(f"├─ {project}: {data['completed_tasks']}/{data['total_tasks']} ({data['completion_rate']}%)")
        
        # Time analysis
        if stats['time_analysis']:
            time_data = stats['time_analysis']
            print(f"\n⏱️  TIME ANALYSIS")
            print(f"├─ Average Completion: {time_data['average_completion_time_hours']} hours")
            print(f"├─ Median Completion: {time_data['median_completion_time_hours']} hours")
            print(f"├─ Fastest: {time_data['fastest_completion_hours']} hours")
            print(f"└─ Slowest: {time_data['slowest_completion_hours']} hours")
        
        # Trends
        if trends:
            print(f"\n📈 TREND ANALYSIS")
            velocity = trends['completion_velocity']
            velocity_emoji = "📈" if velocity > 0 else "📉" if velocity < 0 else "➡️"
            print(f"├─ Completion Velocity: {velocity_emoji} {velocity:.1f} tasks/week")
            
            if trends['recommendations']:
                print(f"\n💡 RECOMMENDATIONS")
                for i, rec in enumerate(trends['recommendations']):
                    prefix = "├─" if i < len(trends['recommendations']) - 1 else "└─"
                    print(f"{prefix} {rec}")
        
        print("\n" + "=" * 60)
        print(f"📊 Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def _generate_json_report(self, stats, trends=None):
        """Generate JSON report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'stats': stats,
            'trends': trends
        }
        return json.dumps(report, indent=2)
    
    def _generate_html_report(self, stats, trends=None):
        """Generate HTML report"""
        metrics = stats['completion_metrics']
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Asana Analytics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .score {{ font-size: 2em; font-weight: bold; text-align: center; padding: 20px; }}
                .projects {{ display: flex; flex-wrap: wrap; gap: 10px; }}
                .project {{ background: #e9f4f9; padding: 10px; border-radius: 3px; min-width: 200px; }}
            </style>
        </head>
        <body>
            <h1>📊 Asana Productivity Analytics</h1>
            <p><strong>Period:</strong> {stats['period']['start_date'][:10]} to {stats['period']['end_date'][:10]}</p>
            
            <div class="score">🎯 Productivity Score: {stats['productivity_score']}/100</div>
            
            <div class="metric">
                <h3>📈 Completion Metrics</h3>
                <p>Total Tasks: <strong>{metrics['total_tasks']}</strong></p>
                <p>Completed: <strong>{metrics['completed_in_period']}</strong></p>
                <p>Completion Rate: <strong>{metrics['completion_rate']}%</strong></p>
                <p>Overdue Tasks: <strong>{metrics['overdue_tasks']}</strong></p>
            </div>
            
            <div class="metric">
                <h3>📁 Project Breakdown</h3>
                <div class="projects">
        """
        
        for project, data in stats['project_breakdown'].items():
            html += f"""
                    <div class="project">
                        <strong>{project}</strong><br>
                        {data['completed_tasks']}/{data['total_tasks']} tasks<br>
                        {data['completion_rate']}% complete
                    </div>
            """
        
        html += """
                </div>
            </div>
            
            <p><em>Report generated on {}</em></p>
        </body>
        </html>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return html


def main():
    parser = argparse.ArgumentParser(description='Asana Analytics Dashboard')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--project', type=str, help='Specific project ID to analyze')
    parser.add_argument('--export', choices=['json', 'csv', 'html'], help='Export format')
    parser.add_argument('--team-stats', action='store_true', help='Include team statistics')
    parser.add_argument('--trend-analysis', action='store_true', help='Include trend analysis')
    
    args = parser.parse_args()
    
    # Get PAT from environment
    pat = os.getenv('ASANA_PAT')
    if not pat:
        print("❌ ASANA_PAT environment variable not set")
        print("Please set it with: export ASANA_PAT='your_personal_access_token'")
        sys.exit(1)
    
    # Initialize analytics
    analytics = AsanaAnalytics(pat)
    
    # Get completion stats
    stats = analytics.get_completion_stats(days=args.days, project_id=args.project)
    
    # Get trend analysis if requested
    trends = None
    if args.trend_analysis:
        trends = analytics.get_trend_analysis(days=args.days)
    
    # Generate and output report
    if args.export:
        report = analytics.generate_report(stats, trends, format=args.export)
        
        filename = f"asana_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.export}"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"\n✅ Report exported to: {filename}")
    else:
        analytics.generate_report(stats, trends, format='console')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
