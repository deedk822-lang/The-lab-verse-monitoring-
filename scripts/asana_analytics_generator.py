import asana
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
from dateutil import parser
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

def get_client():
    pat = os.getenv('ASANA_PAT')
    if not pat:
        print("❌ ASANA_PAT not found")
        return None
    return asana.Client.access_token(pat)

def get_task_history(client, days_back=30):
    """Get task completion history"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    print(f"📅 Analyzing tasks from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    workspaces = list(client.workspaces.find_all())
    if not workspaces:
        return []

    workspace_id = workspaces[0]['gid']
    me = client.users.me()

    # Get completed tasks in the period
    tasks = list(client.tasks.find_by_user(me['gid'], {
        "workspace": workspace_id,
        "opt_fields": "name,completed,completed_at,created_at,due_date,projects.name,assignee.name,tags.name",
        "completed_since": start_date.isoformat()
    }))

    # Also get currently incomplete tasks
    incomplete_tasks = list(client.tasks.find_by_user(me['gid'], {
        "workspace": workspace_id,
        "opt_fields": "name,completed,created_at,due_date,projects.name,assignee.name,tags.name",
        "completed_since": "now"
    }))

    all_tasks = tasks + incomplete_tasks
    print(f"📊 Found {len(all_tasks)} total tasks ({len(tasks)} completed, {len(incomplete_tasks)} incomplete)")

    return all_tasks

def analyze_completion_patterns(tasks):
    """Analyze task completion patterns"""
    analytics = {
        'total_tasks': len(tasks),
        'completed_tasks': 0,
        'incomplete_tasks': 0,
        'overdue_tasks': 0,
        'projects': defaultdict(lambda: {'total': 0, 'completed': 0}),
        'completion_by_day': defaultdict(int),
        'avg_completion_time': 0,
        'tags': defaultdict(int),
        'completion_rate_trend': [],
        'insights': []
    }

    completion_times = []
    today = datetime.now().date()

    for task in tasks:
        # Basic counts
        if task['completed']:
            analytics['completed_tasks'] += 1

            # Completion time analysis
            if task.get('completed_at') and task.get('created_at'):
                created = parser.parse(task['created_at'])
                completed = parser.parse(task['completed_at'])
                completion_time = (completed - created).days
                completion_times.append(completion_time)

                # Daily completion tracking
                completion_date = completed.date()
                analytics['completion_by_day'][str(completion_date)] += 1
        else:
            analytics['incomplete_tasks'] += 1

            # Check if overdue
            if task.get('due_date'):
                due_date = parser.parse(task['due_date']).date()
                if due_date < today:
                    analytics['overdue_tasks'] += 1

        # Project analysis
        for project in task.get('projects', []):
            project_name = project['name']
            analytics['projects'][project_name]['total'] += 1
            if task['completed']:
                analytics['projects'][project_name]['completed'] += 1

        # Tag analysis
        for tag in task.get('tags', []):
            analytics['tags'][tag['name']] += 1

    # Calculate averages
    if completion_times:
        analytics['avg_completion_time'] = sum(completion_times) / len(completion_times)

    # Generate insights
    completion_rate = analytics['completed_tasks'] / analytics['total_tasks'] * 100 if analytics['total_tasks'] > 0 else 0

    analytics['insights'] = [
        f"Overall completion rate: {completion_rate:.1f}%",
        f"Average time to complete: {analytics['avg_completion_time']:.1f} days",
        f"Currently {analytics['overdue_tasks']} overdue tasks"
    ]

    # Project performance insights
    best_project = None
    best_rate = 0
    for project, stats in analytics['projects'].items():
        if stats['total'] >= 3:  # Only consider projects with significant activity
            rate = stats['completed'] / stats['total'] * 100
            if rate > best_rate:
                best_rate = rate
                best_project = project

    if best_project:
        analytics['insights'].append(f"Best performing project: {best_project} ({best_rate:.1f}% completion rate)")

    return analytics

def generate_charts(analytics, include_charts=True):
    """Generate visualization charts"""
    if not include_charts:
        return []

    charts = []

    try:
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

        # 1. Completion Status Pie Chart
        fig, ax = plt.subplots(figsize=(10, 6))
        labels = ['Completed', 'Incomplete', 'Overdue']
        sizes = [analytics['completed_tasks'],
                analytics['incomplete_tasks'] - analytics['overdue_tasks'],
                analytics['overdue_tasks']]
        colors = ['#28a745', '#6c757d', '#dc3545']

        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Task Completion Status', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig('completion_status.png', dpi=150, bbox_inches='tight')
        plt.close()
        charts.append('completion_status.png')

        # 2. Project Performance Bar Chart
        if analytics['projects']:
            fig, ax = plt.subplots(figsize=(12, 8))

            projects = list(analytics['projects'].keys())
            completion_rates = []
            for project in projects:
                stats = analytics['projects'][project]
                rate = stats['completed'] / stats['total'] * 100 if stats['total'] > 0 else 0
                completion_rates.append(rate)

            bars = ax.bar(projects, completion_rates, color='skyblue', edgecolor='navy', alpha=0.7)
            ax.set_title('Completion Rate by Project', fontsize=16, fontweight='bold')
            ax.set_ylabel('Completion Rate (%)', fontsize=12)
            ax.set_xlabel('Projects', fontsize=12)

            # Add value labels on bars
            for bar, rate in zip(bars, completion_rates):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('project_performance.png', dpi=150, bbox_inches='tight')
            plt.close()
            charts.append('project_performance.png')

        # 3. Daily Completion Trend
        if analytics['completion_by_day']:
            fig, ax = plt.subplots(figsize=(14, 6))

            dates = sorted(analytics['completion_by_day'].keys())
            counts = [analytics['completion_by_day'][date] for date in dates]

            ax.plot(dates, counts, marker='o', linewidth=2, markersize=6, color='#007bff')
            ax.set_title('Daily Task Completion Trend', fontsize=16, fontweight='bold')
            ax.set_ylabel('Tasks Completed', fontsize=12)
            ax.set_xlabel('Date', fontsize=12)
            ax.grid(True, alpha=0.3)

            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('completion_trend.png', dpi=150, bbox_inches='tight')
            plt.close()
            charts.append('completion_trend.png')

        print(f"📈 Generated {len(charts)} charts")

    except Exception as e:
        print(f"⚠️ Error generating charts: {str(e)}")

    return charts

def export_data(analytics, tasks):
    """Export data to CSV for further analysis"""
    # Task details export
    task_data = []
    for task in tasks:
        task_data.append({
            'name': task['name'],
            'completed': task['completed'],
            'created_at': task.get('created_at', ''),
            'completed_at': task.get('completed_at', ''),
            'due_date': task.get('due_date', ''),
            'projects': ', '.join([p['name'] for p in task.get('projects', [])]),
            'tags': ', '.join([t['name'] for t in task.get('tags', [])])
        })

    df = pd.DataFrame(task_data)
    df.to_csv('task_details.csv', index=False)

    # Project summary export
    project_data = []
    for project, stats in analytics['projects'].items():
        completion_rate = stats['completed'] / stats['total'] * 100 if stats['total'] > 0 else 0
        project_data.append({
            'project': project,
            'total_tasks': stats['total'],
            'completed_tasks': stats['completed'],
            'completion_rate': completion_rate
        })

    df_projects = pd.DataFrame(project_data)
    df_projects.to_csv('project_summary.csv', index=False)

    print("📋 Exported CSV files: task_details.csv, project_summary.csv")

def generate_html_report(analytics, charts):
    """Generate HTML dashboard report"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asana Analytics Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .metric {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
            .metric-value {{ font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }}
            .metric-label {{ color: #6c757d; font-size: 0.9em; }}
            .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .chart {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
            .insights {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .insight {{ padding: 15px; margin: 10px 0; background: #e3f2fd; border-left: 4px solid #2196f3; border-radius: 5px; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; text-align: center; margin-top: 20px; }}
            h1, h2 {{ color: #2c3e50; }}
            .completed {{ color: #28a745; }}
            .incomplete {{ color: #6c757d; }}
            .overdue {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Asana Analytics Dashboard</h1>
                <p>Comprehensive task completion analysis and insights</p>
            </div>

            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{analytics['total_tasks']}</div>
                    <div class="metric-label">Total Tasks</div>
                </div>
                <div class="metric">
                    <div class="metric-value completed">{analytics['completed_tasks']}</div>
                    <div class="metric-label">Completed</div>
                </div>
                <div class="metric">
                    <div class="metric-value incomplete">{analytics['incomplete_tasks']}</div>
                    <div class="metric-label">Incomplete</div>
                </div>
                <div class="metric">
                    <div class="metric-value overdue">{analytics['overdue_tasks']}</div>
                    <div class="metric-label">Overdue</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{analytics['avg_completion_time']:.1f}</div>
                    <div class="metric-label">Avg Days to Complete</div>
                </div>
            </div>
    """

    if charts:
        html += '<div class="charts">'
        for chart in charts:
            chart_name = chart.replace('.png', '').replace('_', ' ').title()
            html += f'<div class="chart"><h3>{chart_name}</h3><img src="{chart}" alt="{chart_name}" style="max-width: 100%; height: auto;"></div>'
        html += '</div>'

    html += f"""
            <div class="insights">
                <h2>💡 Key Insights</h2>
    """

    for insight in analytics['insights']:
        html += f'<div class="insight">{insight}</div>'

    html += f"""
            </div>

            <div class="timestamp">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </div>
    </body>
    </html>
    """

    with open('analytics_dashboard.html', 'w') as f:
        f.write(html)

    print("🌐 Generated HTML dashboard: analytics_dashboard.html")

def main():
    client = get_client()
    if not client:
        return False

    days_back = int(os.getenv('REPORT_PERIOD', '30'))
    include_charts = os.getenv('INCLUDE_CHARTS', 'true').lower() == 'true'

    print(f"🚀 Generating analytics report for last {days_back} days")

    # Get task data
    tasks = get_task_history(client, days_back)
    if not tasks:
        print("❌ No tasks found")
        return False

    # Analyze patterns
    analytics = analyze_completion_patterns(tasks)

    # Generate visualizations
    charts = generate_charts(analytics, include_charts)

    # Export data
    export_data(analytics, tasks)

    # Generate HTML report
    generate_html_report(analytics, charts)

    # Save analytics JSON
    with open('analytics.json', 'w') as f:
        json.dump(analytics, f, indent=2, default=str)

    # Set outputs
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        completion_rate = analytics['completed_tasks'] / analytics['total_tasks'] * 100 if analytics['total_tasks'] > 0 else 0
        f.write(f"completion_rate={completion_rate:.1f}\n")
        f.write(f"total_tasks={analytics['total_tasks']}\n")
        f.write(f"avg_completion_time={analytics['avg_completion_time']:.1f}\n")
        f.write(f"charts_generated={len(charts)}\n")

    print("✅ Analytics generation complete!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
