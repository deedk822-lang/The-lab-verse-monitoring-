import asana
import sys
import os

def bulk_complete_all_tasks(pat, dry_run=False):
    try:
        client = asana.Client.access_token(pat)

        # Get workspace (use first available)
        workspaces = list(client.workspaces.find_all())
        if not workspaces:
            print("❌ No workspaces found")
            return False, 0

        workspace_id = workspaces[0]['gid']
        print(f"Using workspace: {workspaces[0]['name']}")

        # Get user's tasks across all projects
        me = client.users.me()
        tasks = list(client.tasks.find_by_user(me['gid'], {
            "workspace": workspace_id,
            "opt_fields": "name,completed,projects.name",
            "completed_since": "now"
        }))

        if not tasks:
            print("No incomplete tasks found")
            return True, 0

        print(f"Found {len(tasks)} incomplete tasks")

        completed_count = 0

        for task in tasks:
            if not task['completed']:
                project_names = [p['name'] for p in task.get('projects', [])]
                project_info = f" (Projects: {', '.join(project_names)})" if project_names else ""

                if dry_run:
                    print(f"🧪 WOULD COMPLETE: {task['name']}{project_info}")
                    completed_count += 1
                else:
                    print(f"Completing: {task['name']}{project_info}")
                    client.tasks.update(task['gid'], {'completed': True})
                    completed_count += 1

        print(f"\n📊 Summary:")
        print(f"✅ {'Would complete' if dry_run else 'Completed'}: {completed_count} tasks")
        print(f"🔄 Bulk completion finished")

        return True, completed_count

    except Exception as e:
        print(f"❌ Error in bulk completion: {str(e)}")
        return False, 0

if __name__ == "__main__":
    pat = os.environ["ASANA_PAT"]
    dry_run = os.environ["DRY_RUN"] == "true"

    if not pat:
        print("❌ ASANA_PAT secret not found. Please add your Asana Personal Access Token to repository secrets.")
        sys.exit(1)

    if not dry_run:
        print("⚠️  WARNING: This will complete ALL your incomplete tasks!")
        print("Make sure this is what you want to do.")

    success, completed_count = bulk_complete_all_tasks(pat, dry_run)

    # Set outputs for GitHub Actions
    with open(os.getenv('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
        f.write(f"completed-count={completed_count}\n")

    sys.exit(0 if success else 1)
