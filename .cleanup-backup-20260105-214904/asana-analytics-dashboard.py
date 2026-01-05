#!/usr/bin/env python3
"""
Asana Analytics Dashboard (Improved Version)

This script generates comprehensive analytics and reports for Asana task completion
metrics, helping you track productivity, identify trends, and optimize workflows.

This version has been refactored for major performance improvements, especially in
trend analysis, and includes previously missing features like team stats and CSV export.

Usage:
    python asana-analytics-dashboard.py [--days DAYS] [--project PROJECT_ID] [--export FORMAT] [--team-stats] [--trend-analysis]

Environment Variables:
    ASANA_PAT          Your Asana Personal Access Token
"""

import asana
import os
import sys
import json
import csv
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dateutil.parser import parse
import statistics

class AsanaAnalytics:
    """A class to handle Asana analytics and reporting."""

    def __init__(self, pat):
        try:
            self.client = asana.Client.access_token(pat)
            me = self.client.users.get_user('me')
            self.user_id = me['gid']
            self.workspace_id = me['workspaces'][0]['gid']
            print(f"✅ Authenticated as: {me['name']}")
            print(f"✅ Connected to workspace: {me['workspaces'][0]['name']}")
        except asana.error.InvalidTokenError:
            print("❌ Error: Invalid Asana Personal Access Token (ASANA_PAT).")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            sys.exit(1)

    def _fetch_tasks(self, days=30, project_id=None):
        """Fetches all relevant tasks in a single API call for the given period."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        print(f"\n🔍 Fetching tasks from the last {days} days...")

        try:
            if project_id:
                return list(self.client.tasks.get_tasks_for_project(
                    project_id,
                    completed_since=start_date.isoformat(),
                    opt_fields="name,completed,completed_at,created_at,due_on,assignee.name,projects.name"
                ))
            else:
                return list(self.client.tasks.get_tasks_for_user_task_list(
                    self.user_id,
                    {
                        "workspace": self.workspace_id,
                        "completed_since": start_date.isoformat(),
                        "opt_fields": "name,completed,completed_at,created_at,due_on,assignee.name,projects.name"
                    }
                ))
        except asana.error.AsanaError as e:
            print(f"❌ Asana API Error while fetching tasks: {e}")
            return []

    def process_task_data(self, tasks, days=30):
        """Processes a list of raw task data into structured analytics."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        end_date = datetime.now(timezone.utc)

        completed_tasks, overdue_tasks = [], []
        daily_completions = defaultdict(int)
        project_stats = defaultdict(lambda: {'completed': 0, 'total': 0})
        completion_times = []

        for task in tasks:
            is_completed_in_period = False
            if task.get('completed') and task.get('completed_at'):
                completed_at = parse(task['completed_at'])
                if start_date <= completed_at <= end_date:
                    completed_tasks.append(task)
                    is_completed_in_period = True
                    daily_completions[completed_at.date().isoformat()] += 1
                    if task.get('created_at'):
                        created_at = parse(task['created_at'])
                        time_diff_hours = (completed_at - created_at).total_seconds() / 3600
                        completion_times.append(time_diff_hours)

            if not task.get('completed') and task.get('due_on'):
                if parse(task['due_on']).date() < end_date.date():
                    overdue_tasks.append(task)

            for project in task.get('projects', []):
                project_stats[project['name']]['total'] += 1
                if is_completed_in_period:
                    project_stats[project['name']]['completed'] += 1
        
        # --- Calculate Final Metrics ---
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        # --- Calculate Productivity Score ---
        overdue_penalty = (len(overdue_tasks) / max(total_tasks, 1) * 100)
        daily_bonus = (completed_count / max(days, 1)) * 10
        productivity_score = statistics.mean([
            min(completion_rate, 100),
            max(0, 100 - overdue_penalty),
            min(100, daily_bonus)
        ])

        stats = {
            'period': {'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(), 'days': days},
            'completion_metrics': {
                'total_tasks': total_tasks,
                'completed_in_period': completed_count,
                'overdue_tasks': len(overdue_tasks),
                'completion_rate': round(completion_rate, 2),
                'average_daily_completions': round(completed_count / days, 2)
            },
            'daily_breakdown': dict(sorted(daily_completions.items())),
            'project_breakdown': self._calculate_project_rates(project_stats),
            'time_analysis': self._analyze_completion_times(completion_times),
            'productivity_score': round(productivity_score, 2)
        }
        return stats

    def get_team_stats(self, project_id):
        """[NEW] Get task completion stats for each team member in a project."""
        if not project_id:
            print("⚠️ --team-stats requires a --project to be specified.")
            return None
        print("\n👥 Analyzing team stats...")
        try:
            project_members = self.client.projects.get_project(project_id, fields="team.name,followers.name")
            users = project_members.get('followers', [])
            tasks = self._fetch_tasks(project_id=project_id)
            
            team_stats = defaultdict(lambda: {'completed': 0, 'total': 0})
            for task in tasks:
                if task.get('assignee'):
                    assignee_name = task['assignee']['name']
                    team_stats[assignee_name]['total'] += 1
                    if task.get('completed'):
                        team_stats[assignee_name]['completed'] += 1
            
            return {user['name']: data for user, data in zip(users, team_stats.values())}
        except asana.error.AsanaError as e:
            print(f"❌ Asana API Error while fetching team stats: {e}")
            return None

    def get_trend_analysis(self, tasks, days=30):
        """[IMPROVED] Analyze trends over time from a single dataset."""
        print(f"\n📈 Analyzing trends over the last {days} days...")
        weekly_completions = defaultdict(int)
        now = datetime.now(timezone.utc)

        for task in tasks:
            if task.get('completed') and task.get('completed_at'):
                completed_at = parse(task['completed_at'])
                weeks_ago = (now - completed_at).days // 7
                if 0 <= weeks_ago < (days // 7):
                    weekly_completions[weeks_ago] += 1
        
        sorted_weeks = sorted(weekly_completions.items())
        weekly_trends = [{'week': f"{k} weeks ago", 'completions': v} for k, v in sorted_weeks]

        # Calculate velocity
        recent_completions = [v for k, v in sorted_weeks if k < 2] # Last 2 weeks
        velocity = statistics.mean(recent_completions) - statistics.mean([v for k,v in sorted_weeks if k >=2]) if len(recent_completions) > 1 else 0

        return {'weekly_trends': weekly_trends, 'completion_velocity': round(velocity, 2)}

    # --- Helper Methods ---
    def _calculate_project_rates(self, project_stats):
        """Helper to calculate completion rates for projects."""
        rates = {}
        for name, data in project_stats.items():
            rate = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
            rates[name] = {'completed': data['completed'], 'total': data['total'], 'rate': round(rate, 2)}
        return rates

    def _analyze_completion_times(self, times):
        """Helper to analyze task completion times."""
        if not times: return {}
        return {
            'average_hours': round(statistics.mean(times), 2),
            'median_hours': round(statistics.median(times), 2),
            'fastest_hours': round(min(times), 2),
            'slowest_hours': round(max(times), 2)
        }

    # --- Reporting Methods ---
    def generate_report(self, stats, trends=None, team_stats=None, format='console'):
        """Generate formatted report based on the specified format."""
        filename = f"asana_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        report_content = ""

        if format == 'console':
            self._print_console_report(stats, trends, team_stats)
            return

        if format == 'json':
            report_content = json.dumps({'stats': stats, 'trends': trends, 'team_stats': team_stats}, indent=2)
        elif format == 'csv':
            report_content = self._generate_csv_report(stats, team_stats)
        elif format == 'html':
            report_content = self._generate_html_report(stats, trends, team_stats)
        
        with open(filename, 'w', newline='') as f:
            f.write(report_content)
        print(f"\n✅ Report exported to: {filename}")

    def _print_console_report(self, stats, trends, team_stats):
        """Prints a formatted report to the console."""
        print("\n" + "=" * 60 + "\n📊 ASANA PRODUCTIVITY ANALYTICS REPORT\n" + "=" * 60)
        print(f"\n📅 Analysis Period: {stats['period']['start_date'][:10]} to {stats['period']['end_date'][:10]}")
        
        score = stats['productivity_score']
        score_emoji = "🔥" if score >= 80 else "✅" if score >= 60 else "⚠️"
        print(f"\n🎯 PRODUCTIVITY SCORE: {score_emoji} {score}/100")

        metrics = stats['completion_metrics']
        print("\n📈 COMPLETION METRICS")
        for key, value in metrics.items():
            print(f"├─ {key.replace('_', ' ').title()}: {value}{'%' if 'rate' in key else ''}")

        if stats['project_breakdown']:
            print("\n📁 PROJECT BREAKDOWN")
            for project, data in stats['project_breakdown'].items():
                print(f"├─ {project}: {data['completed']}/{data['total']} tasks ({data['rate']}%)")
        
        if team_stats:
            print("\n👥 TEAM STATS")
            for member, data in team_stats.items():
                print(f"├─ {member}: {data['completed']}/{data['total']} tasks")

        if trends and trends['weekly_trends']:
            print("\n📈 TREND ANALYSIS")
            for week in trends['weekly_trends']:
                print(f"├─ {week['week']}: {week['completions']} completions")
            velocity_emoji = "📈" if trends['completion_velocity'] > 0 else "📉"
            print(f"└─ Velocity: {velocity_emoji} {trends['completion_velocity']} tasks/week trend")
        
        print("\n" + "=" * 60)

    def _generate_csv_report(self, stats, team_stats):
        """[NEW] Generates a CSV report."""
        from io import StringIO
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Metric', 'Value', 'Details'])
        # Main stats
        for key, value in stats['completion_metrics'].items():
            writer.writerow([key, value, 'Overall'])
        writer.writerow(['productivity_score', stats['productivity_score'], 'Overall'])
        # Project stats
        for proj, data in stats['project_breakdown'].items():
            writer.writerow(['project_completed_tasks', data['completed'], proj])
            writer.writerow(['project_total_tasks', data['total'], proj])
            writer.writerow(['project_completion_rate', data['rate'], proj])
        # Team stats
        if team_stats:
            for member, data in team_stats.items():
                writer.writerow(['team_completed_tasks', data['completed'], member])
                writer.writerow(['team_total_tasks', data['total'], member])
        
        return output.getvalue()

    def _generate_html_report(self, stats, trends, team_stats):
        """Generates an HTML report."""
        # This is a simplified example; can be expanded with charts, etc.
        html = f"<h1>📊 Asana Report</h1><p>Period: {stats['period']['start_date'][:10]} to {stats['period']['end_date'][:10]}</p>"
        html += f"<h2>🎯 Productivity Score: {stats['productivity_score']}/100</h2>"
        html += "<h3>📈 Completion Metrics</h3><ul>"
        for k, v in stats['completion_metrics'].items():
            html += f"<li>{k.replace('_', ' ').title()}: {v}{'%' if 'rate' in k else ''}</li>"
        html += "</ul>"
        # Add more sections for projects, team, trends...
        return html


def main():
    """Main function to parse arguments and run the analytics."""
    parser = argparse.ArgumentParser(description='Asana Analytics Dashboard')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--project', type=str, help='Specific project ID to analyze')
    parser.add_argument('--export', choices=['json', 'csv', 'html'], help='Export format')
    parser.add_argument('--team-stats', action='store_true', help='Include team statistics for the specified project')
    parser.add_argument('--trend-analysis', action='store_true', help='Include trend analysis')
    
    args = parser.parse_args()
    
    pat = os.getenv('ASANA_PAT')
    if not pat:
        print("❌ ASANA_PAT environment variable not set.")
        sys.exit(1)
    
    analytics = AsanaAnalytics(pat)
    
    # Fetch the core data once
    tasks = analytics._fetch_tasks(days=args.days, project_id=args.project)
    if not tasks:
        print("ℹ️ No tasks found for the specified criteria. Exiting.")
        return

    # Process data to get stats
    stats = analytics.process_task_data(tasks, days=args.days)
    
    # Get additional analysis if requested
    trends = analytics.get_trend_analysis(tasks, days=args.days) if args.trend_analysis else None
    team_stats = analytics.get_team_stats(project_id=args.project) if args.team_stats else None
    
    # Generate the final report
    analytics.generate_report(stats, trends, team_stats, format=args.export or 'console')


if __name__ == "__main__":
    main()
