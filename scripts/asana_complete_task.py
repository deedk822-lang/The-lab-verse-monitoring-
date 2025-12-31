import asana
import sys
import os
import json

def check_task_dependencies(client, task_id):
    """Check if task has incomplete dependencies"""
    try:
        task = client.tasks.find_by_id(task_id, {"opt_fields": "dependencies.completed,dependencies.name"})
        incomplete_deps = []

        for dep in task.get('dependencies', []):
            if not dep.get('completed', True):
                incomplete_deps.append(dep['name'])

        return incomplete_deps
    except:
        return []

def backup_task_info(client, task_id):
    """Backup task information before completion"""
    try:
        task = client.tasks.find_by_id(task_id, {
            "opt_fields": "name,notes,completed,due_date,assignee.name,projects.name,tags.name,created_at,modified_at"
        })

        backup_data = {
            "id": task_id,
            "name": task['name'],
            "notes": task.get('notes', ''),
            "completed": task['completed'],
            "due_date": task.get('due_date'),
            "assignee": task.get('assignee', {}).get('name'),
            "projects": [p['name'] for p in task.get('projects', [])],
            "tags": [t['name'] for t in task.get('tags', [])],
            "created_at": task.get('created_at'),
            "modified_at": task.get('modified_at'),
            "backup_timestamp": task.get('modified_at')
        }

        with open(f'task_backup_{task_id}.json', 'w') as f:
            json.dump(backup_data, f, indent=2)

        return backup_data
    except Exception as e:
        print(f"Warning: Could not backup task info: {str(e)}")
        return None

def complete_task(task_id, pat, dry_run=False, check_deps=False):
    try:
        client = asana.Client.access_token(pat)

        # Get task details first
        task = client.tasks.find_by_id(task_id, {"opt_fields": "name,completed"})
        print(f"Task found: {task['name']}")

        if task['completed']:
            print(f"Task '{task['name']}' is already completed.")
            return True, task['name'], 0

        # Check dependencies if requested
        if check_deps:
            incomplete_deps = check_task_dependencies(client, task_id)
            if incomplete_deps:
                print(f"⚠️  Task has incomplete dependencies:")
                for dep in incomplete_deps:
                    print(f"   - {dep}")
                print(f"Skipping completion due to dependencies.")
                return True, task['name'], 0

        if dry_run:
            print(f"🧪 DRY RUN: Would complete task '{task['name']}'")
            return True, task['name'], 1

        # Backup task information
        print("📄 Backing up task information...")
        backup_task_info(client, task_id)

        # Mark task as complete
        result = client.tasks.update(task_id, {'completed': True})
        print(f"✅ Successfully completed task: {task['name']}")
        return True, task['name'], 1

    except Exception as e:
        print(f"❌ Error completing task {task_id}: {str(e)}")
        return False, None, 0

if __name__ == "__main__":
    task_id = os.environ["TASK_ID"]
    pat = os.environ["ASANA_PAT"]
    dry_run = os.environ["DRY_RUN"] == "true"
    check_deps = os.environ["CHECK_DEPENDENCIES"] == "true"

    if not pat:
        print("❌ ASANA_PAT secret not found. Please add your Asana Personal Access Token to repository secrets.")
        sys.exit(1)

    success, task_name, completed_count = complete_task(task_id, pat, dry_run, check_deps)

    # Set outputs for GitHub Actions
    with open(os.getenv('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
        f.write(f"completed-count={completed_count}\n")
        f.write(f"task-name={task_name or 'Unknown'}\n")

    sys.exit(0 if success else 1)
