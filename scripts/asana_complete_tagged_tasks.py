import asana
import sys
import os

def complete_tagged_tasks(tag_name, pat, dry_run=False):
    try:
        client = asana.Client.access_token(pat)

        # Get workspace (use first available)
        workspaces = list(client.workspaces.find_all())
        if not workspaces:
            print("❌ No workspaces found")
            return False, 0, 0

        workspace_id = workspaces[0]['gid']
        print(f"Using workspace: {workspaces[0]['name']}")

        # Find the tag
        tags = list(client.tags.find_by_workspace(workspace_id, {"opt_fields": "name"}))
        target_tag = None

        for tag in tags:
            if tag['name'].lower() == tag_name.lower():
                target_tag = tag
                break

        if not target_tag:
            print(f"❌ Tag '{tag_name}' not found in workspace")
            return False, 0, 0

        print(f"Found tag: {target_tag['name']}")

        # Get tasks with this tag
        tasks = list(client.tasks.find_by_tag(target_tag['gid'], {"opt_fields": "name,completed"}))

        if not tasks:
            print(f"No tasks found with tag '{tag_name}'")
            return True, 0, 0

        completed_count = 0
        skipped_count = 0

        for task in tasks:
            if not task['completed']:
                if dry_run:
                    print(f"🧪 WOULD COMPLETE: {task['name']}")
                    completed_count += 1
                else:
                    print(f"Completing: {task['name']}")
                    client.tasks.update(task['gid'], {'completed': True})
                    completed_count += 1
            else:
                skipped_count += 1

        print(f"\n📊 Summary:")
        print(f"✅ {'Would complete' if dry_run else 'Completed'}: {completed_count} tasks")
        print(f"⏭️  Skipped (already complete): {skipped_count} tasks")
        print(f"🏷️  Tag: {tag_name}")

        return True, completed_count, skipped_count

    except Exception as e:
        print(f"❌ Error processing tasks with tag '{tag_name}': {str(e)}")
        return False, 0, 0

if __name__ == "__main__":
    tag_name = os.environ["TAG_NAME"]
    pat = os.environ["ASANA_PAT"]
    dry_run = os.environ["DRY_RUN"] == "true"

    if not pat:
        print("❌ ASANA_PAT secret not found. Please add your Asana Personal Access Token to repository secrets.")
        sys.exit(1)

    success, completed_count, skipped_count = complete_tagged_tasks(tag_name, pat, dry_run)

    # Set outputs for GitHub Actions
    with open(os.getenv('GITHUB_OUTPUT', '/dev/stdout'), 'a') as f:
        f.write(f"completed-count={completed_count}\n")
        f.write(f"skipped-count={skipped_count}\n")

    sys.exit(0 if success else 1)
