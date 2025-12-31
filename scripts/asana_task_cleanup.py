import asana
import sys
import os
from datetime import datetime, timedelta
from dateutil import parser
import json

def get_client():
    pat = os.getenv('ASANA_PAT')
    if not pat:
        print("❌ ASANA_PAT not found")
        return None
    return asana.Client.access_token(pat)

def is_overdue_task(task):
    """Check if task is overdue"""
    if not task.get('due_date'):
        return False

    due_date = parser.parse(task['due_date']).date()
    today = datetime.now().date()
    return due_date < today

def has_ready_tag(task, client):
    """Check if task has 'ready-for-completion' tag"""
    try:
        task_details = client.tasks.find_by_id(task['gid'], {"opt_fields": "tags.name"})
        tags = [tag['name'].lower() for tag in task_details.get('tags', [])]
        return any('ready' in tag or 'complete' in tag for tag in tags)
    except:
        return False

def has_completed_subtasks(task, client):
    """Check if task has all subtasks completed (indicating main task ready)"""
    try:
        subtasks = list(client.tasks.subtasks(task['gid'], {"opt_fields": "completed"}))
        if not subtasks:  # No subtasks
            return False
        return all(subtask['completed'] for subtask in subtasks)
    except:
        return False

def should_complete_task(task, criteria, client):
    """Determine if task should be completed based on criteria"""
    if task['completed']:
        return False, "Already completed"

    if criteria == 'overdue':
        if is_overdue_task(task):
            return True, "Overdue task"
    elif criteria == 'ready_tag':
        if has_ready_tag(task, client):
            return True, "Has ready tag"
    elif criteria == 'old_completed_subtasks':
        if has_completed_subtasks(task, client):
            return True, "All subtasks completed"

    return False, "Does not meet criteria"

def run_cleanup():
    dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
    criteria = os.getenv('COMPLETION_CRITERIA', 'overdue')

    print(f"🔍 Running {'DRY RUN' if dry_run else 'LIVE'} cleanup")
    print(f"📋 Criteria: {criteria}")
    print("=" * 60)

    client = get_client()
    if not client:
        return False

    # Get user's workspaces
    workspaces = list(client.workspaces.find_all())
    if not workspaces:
        print("❌ No workspaces found")
        return False

    workspace_id = workspaces[0]['gid']
    print(f"🏢 Workspace: {workspaces[0]['name']}")

    # Get user's tasks
    me = client.users.me()
    tasks = list(client.tasks.find_by_user(me['gid'], {
        "workspace": workspace_id,
        "opt_fields": "name,completed,due_date,projects.name,assignee.name",
        "completed_since": "now"  # Only incomplete tasks
    }))

    print(f"📊 Found {len(tasks)} incomplete tasks")

    completed_count = 0
    skipped_count = 0
    error_count = 0

    completion_log = []

    for task in tasks:
        should_complete, reason = should_complete_task(task, criteria, client)

        project_names = [p['name'] for p in task.get('projects', [])]
        project_info = f" (Projects: {', '.join(project_names)})" if project_names else ""

        if should_complete:
            if dry_run:
                print(f"🔍 WOULD COMPLETE: {task['name']}{project_info}")
                print(f"   Reason: {reason}")
                completion_log.append({
                    "task": task['name'],
                    "reason": reason,
                    "projects": project_names,
                    "action": "would_complete"
                })
                completed_count += 1
            else:
                try:
                    client.tasks.update(task['gid'], {'completed': True})
                    print(f"✅ COMPLETED: {task['name']}{project_info}")
                    print(f"   Reason: {reason}")
                    completion_log.append({
                        "task": task['name'],
                        "reason": reason,
                        "projects": project_names,
                        "action": "completed"
                    })
                    completed_count += 1
                except Exception as e:
                    print(f"❌ ERROR: {task['name']}{project_info}")
                    print(f"   Error: {str(e)}")
                    completion_log.append({
                        "task": task['name'],
                        "error": str(e),
                        "projects": project_names,
                        "action": "error"
                    })
                    error_count += 1
        else:
            skipped_count += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 CLEANUP SUMMARY")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
    print(f"Criteria: {criteria}")
    print(f"✅ {'Would complete' if dry_run else 'Completed'}: {completed_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Set outputs for GitHub Actions
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"completed_count={completed_count}\n")
        f.write(f"skipped_count={skipped_count}\n")
        f.write(f"error_count={error_count}\n")

    # Save detailed log
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "mode": "dry_run" if dry_run else "live",
        "criteria": criteria,
        "summary": {
            "completed": completed_count,
            "skipped": skipped_count,
            "errors": error_count
        },
        "details": completion_log
    }

    with open('cleanup_log.json', 'w') as f:
        json.dump(log_data, f, indent=2)

    return True

if __name__ == "__main__":
    success = run_cleanup()
    sys.exit(0 if success else 1)
