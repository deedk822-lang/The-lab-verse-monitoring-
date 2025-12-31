import asana
import sys
import os
import json

def complete_project_tasks(project_id, pat, dry_run=False):
    try:
        client = asana.Client.access_token(pat)

        # Get project details
        project = client.projects.find_by_id(project_id, {"opt_fields": "name"})
        print(f"Processing project: {project['name']}")

        # Get all tasks in project
        tasks = list(client.tasks.find_by_project(project_id, {"opt_fields": "name,completed,due_date"}))

        if not tasks:
            print("No tasks found in project")
            return True, project['name'], 0, 0

        completed_count = 0
        skipped_count = 0
        task_list = []

        for task in tasks:
            task_info = {
                "name": task['name'],
                "id": task['gid'],
                "due_date": task.get('due_date'),
                "was_completed": task['completed']
            }

            if not task['completed']:
                if dry_run:
                    print(f"🧪 WOULD COMPLETE: {task['name']}")
                    task_info["action"] = "would_complete"
                    completed_count += 1
                else:
                    print(f"Completing: {task['name']}")
                    client.tasks.update(task['gid'], {'completed': True})
                    task_info["action"] = "completed"
                    completed_count += 1
            else:
                task_info["action"] = "already_completed"
                skipped_count += 1

            task_list.append(task_info)

        # Save project completion report
        report = {
            "project_name": project['name'],
            "project_id": project_id,
            "dry_run": dry_run,
            "completed_count": completed_count,
            "skipped_count": skipped_count,
            "total_tasks": len(tasks),
            "tasks": task_list
        }

        with open(f'project_completion_{project_id}.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Summary:")
        print(f"✅ {'Would complete' if dry_run else 'Completed'}: {completed_count} tasks")
        print(f"⏭️  Skipped (already complete): {skipped_count} tasks")
        print(f"📁 Project: {project['name']}")

        return True, project['name'], completed_count, skipped_count

    except Exception as e:
        print(f"❌ Error processing project {project_id}: {str(e)}")
        return False, None, 0, 0

if __name__ == "__main__":
    project_id = os.environ["PROJECT_ID"]
    pat = os.environ["ASANA_PAT"]
    dry_run = os.environ["DRY_RUN"] == "true"

    if not pat:
        print("❌ ASANA_PAT secret not found. Please add your Asana Personal Access Token to repository secrets.")
        sys.exit(1)

    success, project_name, completed_count, skipped_count = complete_project_tasks(project_id, pat, dry_run)

    # Set outputs for GitHub Actions
    with open(os.getenv('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
        f.write(f"completed-count={completed_count}\n")
        f.write(f"skipped-count={skipped_count}\n")
        f.write(f"project-name={project_name or 'Unknown'}\n")

    sys.exit(0 if success else 1)
