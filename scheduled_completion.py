# File: scripts/scheduled_completion.py
import asana
import sys
import os
from datetime import datetime
from dateutil.parser import parse
import json

def get_client():
    """Initializes and returns the Asana client using the PAT."""
    pat = os.getenv('ASANA_PAT')
    if not pat:
        print("❌ ASANA_PAT secret not found in environment variables.")
        return None
    return asana.Client.access_token(pat)

def should_complete_task(task, criteria, client):
    """Determines if a task should be completed based on the given criteria."""
    if task.get('completed'):
        return False, "Already completed"

    now = datetime.now().date()

    if criteria == 'overdue_tasks':
        if task.get('due_on') and parse(task['due_on']).date() < now:
            return True, "Overdue task"

    elif criteria == 'tagged_ready':
        try:
            task_details = client.tasks.get_task(task['gid'], fields=["tags.name"])
            tags = {tag['name'].lower() for tag in task_details.get('tags', [])}
            if 'ready' in tags or 'complete' in tags:
                return True, "Tagged as ready for completion"
        except asana.error.AsanaError as e:
            return False, f"API Error checking tags: {e}"

    elif criteria == 'low_priority':
        created_at = parse(task.get('created_at')).date()
        if (now - created_at).days > 30:
            return True, "Low priority old task (older than 30 days)"

    elif criteria == 'old_completed_projects':
        if any(p.get('completed') for p in task.get('projects', [])):
            return True, "Task in a completed project"

    return False, "Does not meet criteria"

def main():
    """Main function to run the Asana task completion logic."""
    client = get_client()
    if not client:
        sys.exit(1)

    criteria = os.getenv('COMPLETION_CRITERIA', 'overdue_tasks')
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    print(f"🔄 Scheduled completion running...")
    print(f"📋 Criteria: {criteria}")
    print(f"🧪 Dry run: {dry_run}")
    print("-" * 50)

    try:
        me = client.users.get_user('me')
        workspace_id = me['workspaces'][0]['gid']

        tasks = client.tasks.get_tasks({
            'assignee': 'me',
            'workspace': workspace_id,
            'completed_since': 'now',
            'opt_fields': 'name,completed,due_on,created_at,projects.name,projects.completed'
        })

        completed_count = 0
        skipped_count = 0
        processed_tasks = []

        for task in tasks:
            should_complete, reason = should_complete_task(task, criteria, client)
            action = "skipped"

            if should_complete:
                if dry_run:
                    action = "would_complete"
                    print(f"🧪 WOULD COMPLETE: {task['name']} - {reason}")
                    completed_count += 1
                else:
                    try:
                        client.tasks.update_task(task['gid'], {'completed': True})
                        action = "completed"
                        print(f"✅ COMPLETED: {task['name']} - {reason}")
                        completed_count += 1
                    except asana.error.AsanaError as e:
                        action = "failed"
                        print(f"❌ FAILED to complete {task['name']}: {e}")
            else:
                skipped_count += 1

            processed_tasks.append({"name": task['name'], "id": task['gid'], "reason": reason, "action": action})

        print("\n📊 SUMMARY:")
        print(f"✅ {'Would complete' if dry_run else 'Completed'}: {completed_count}")
        print(f"⏭️ Skipped: {skipped_count}")
        print(f"📋 Total processed: {len(processed_tasks)}")

        # Write outputs for subsequent GitHub Actions steps
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write(f"completed-count={completed_count}\n")
                f.write(f"skipped-count={skipped_count}\n")
                f.write(f"total-processed={len(processed_tasks)}\n")

        # Save detailed JSON results for artifacts
        results = {
            "timestamp": datetime.now().isoformat(),
            "criteria": criteria,
            "dry_run": dry_run,
            "summary": {"completed": completed_count, "skipped": skipped_count, "total": len(processed_tasks)},
            "tasks": processed_tasks
        }
        with open('completion_results.json', 'w') as f:
            json.dump(results, f, indent=2)

    except asana.error.AsanaError as e:
        print(f"❌ An Asana API error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
