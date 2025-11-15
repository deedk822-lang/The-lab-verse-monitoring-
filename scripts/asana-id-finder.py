#!/usr/bin/env python3
"""
Asana ID Finder

This script helps you find Asana project IDs, task IDs, and tag names
for use with the GitHub Actions workflow.

Usage:
    python asana-id-finder.py

Make sure to set your ASANA_PAT environment variable first:
    export ASANA_PAT="your_personal_access_token_here"
"""

import asana
import os
import sys
from typing import List, Dict, Optional


def get_client() -> Optional[asana.Client]:
    """
    Create and return an Asana client using the PAT from environment.
    """
    pat = os.getenv('ASANA_PAT')
    if not pat:
        print("❌ Error: ASANA_PAT environment variable not set.")
        print("Please set it with: export ASANA_PAT='your_personal_access_token'")
        return None
    
    try:
        client = asana.Client.access_token(pat)
        return client
    except Exception as e:
        print(f"❌ Error creating Asana client: {str(e)}")
        return None


def list_workspaces(client: asana.Client) -> List[Dict]:
    """
    List all available workspaces.
    """
    try:
        workspaces = list(client.workspaces.find_all())
        return workspaces
    except Exception as e:
        print(f"❌ Error fetching workspaces: {str(e)}")
        return []


def list_projects(client: asana.Client, workspace_id: str) -> List[Dict]:
    """
    List all projects in a workspace.
    """
    try:
        projects = list(client.projects.find_by_workspace(
            workspace_id, 
            {"opt_fields": "name,modified_at,owner.name,team.name"}
        ))
        return projects
    except Exception as e:
        print(f"❌ Error fetching projects: {str(e)}")
        return []


def list_recent_tasks(client: asana.Client, project_id: str, limit: int = 10) -> List[Dict]:
    """
    List recent tasks in a project.
    """
    try:
        tasks = list(client.tasks.find_by_project(
            project_id,
            {"opt_fields": "name,completed,due_date,assignee.name"}
        ))
        return tasks[:limit]
    except Exception as e:
        print(f"❌ Error fetching tasks: {str(e)}")
        return []


def list_tags(client: asana.Client, workspace_id: str) -> List[Dict]:
    """
    List all tags in a workspace.
    """
    try:
        tags = list(client.tags.find_by_workspace(
            workspace_id,
            {"opt_fields": "name,color"}
        ))
        return tags
    except Exception as e:
        print(f"❌ Error fetching tags: {str(e)}")
        return []


def main():
    print("🚀 Asana ID Finder")
    print("=" * 50)
    
    # Create client
    client = get_client()
    if not client:
        sys.exit(1)
    
    # Get workspaces
    print("\n🏢 Fetching workspaces...")
    workspaces = list_workspaces(client)
    
    if not workspaces:
        print("❌ No workspaces found.")
        sys.exit(1)
    
    print(f"\n📊 Found {len(workspaces)} workspace(s):")
    for i, workspace in enumerate(workspaces, 1):
        print(f"  {i}. {workspace['name']} (ID: {workspace['gid']})")
    
    # Select workspace
    if len(workspaces) == 1:
        selected_workspace = workspaces[0]
        print(f"\n✅ Using workspace: {selected_workspace['name']}")
    else:
        try:
            choice = int(input(f"\nSelect workspace (1-{len(workspaces)}): ")) - 1
            selected_workspace = workspaces[choice]
        except (ValueError, IndexError):
            print("❌ Invalid selection.")
            sys.exit(1)
    
    workspace_id = selected_workspace['gid']
    
    # Get projects
    print(f"\n📁 Fetching projects in '{selected_workspace['name']}'...")
    projects = list_projects(client, workspace_id)
    
    if not projects:
        print("❌ No projects found.")
        sys.exit(1)
    
    print(f"\n📊 Found {len(projects)} project(s):")
    print("-" * 80)
    for project in projects:
        owner = project.get('owner', {}).get('name', 'No owner')
        team = project.get('team', {}).get('name', 'No team')
        print(f"  📁 {project['name']}")
        print(f"     ID: {project['gid']}")
        print(f"     Owner: {owner} | Team: {team}")
        print()
    
    # Ask if user wants to see tasks for a specific project
    show_tasks = input("\nDo you want to see tasks for a specific project? (y/n): ").lower().strip()
    
    if show_tasks == 'y':
        project_name = input("Enter project name (partial match OK): ").strip().lower()
        matching_projects = [p for p in projects if project_name in p['name'].lower()]
        
        if matching_projects:
            if len(matching_projects) == 1:
                selected_project = matching_projects[0]
            else:
                print(f"\nFound {len(matching_projects)} matching projects:")
                for i, project in enumerate(matching_projects, 1):
                    print(f"  {i}. {project['name']}")
                
                try:
                    choice = int(input(f"Select project (1-{len(matching_projects)}): ")) - 1
                    selected_project = matching_projects[choice]
                except (ValueError, IndexError):
                    print("❌ Invalid selection.")
                    selected_project = None
            
            if selected_project:
                print(f"\n📋 Recent tasks in '{selected_project['name']}':")
                print("-" * 80)
                tasks = list_recent_tasks(client, selected_project['gid'])
                
                if tasks:
                    for task in tasks:
                        status = "✅" if task['completed'] else "🔴"
                        assignee = task.get('assignee', {}).get('name', 'Unassigned') if task.get('assignee') else 'Unassigned'
                        due_date = task.get('due_date', 'No due date')
                        
                        print(f"  {status} {task['name']}")
                        print(f"     ID: {task['gid']}")
                        print(f"     Assignee: {assignee} | Due: {due_date}")
                        print()
                else:
                    print("  No tasks found in this project.")
        else:
            print(f"❌ No projects found matching '{project_name}'")
    
    # Get tags
    print(f"\n🏷️ Fetching tags in '{selected_workspace['name']}'...")
    tags = list_tags(client, workspace_id)
    
    if tags:
        print(f"\n📊 Found {len(tags)} tag(s):")
        print("-" * 40)
        for tag in tags:
            color = tag.get('color', 'no color')
            print(f"  🏷️ {tag['name']} ({color})")
    else:
        print("❌ No tags found.")
    
    # Summary
    print("\n" + "=" * 50)
    print("📝 SUMMARY FOR GITHUB WORKFLOW")
    print("=" * 50)
    print(f"Workspace: {selected_workspace['name']}")
    print(f"Workspace ID: {workspace_id}")
    print(f"\nProject IDs (copy for workflow):")
    for project in projects[:5]:  # Show top 5 projects
        print(f"  {project['name']}: {project['gid']}")
    
    if len(projects) > 5:
        print(f"  ... and {len(projects) - 5} more projects")
    
    print("\n🛠️ HOW TO USE WITH GITHUB WORKFLOW:")
    print("1. Go to your repository's Actions tab")
    print("2. Select 'Complete Asana Tasks' workflow")
    print("3. Click 'Run workflow'")
    print("4. Use the IDs shown above")
    
    print("\n🔗 Useful Links:")
    print(f"- Your workspace: https://app.asana.com/0/{workspace_id}/list")
    if projects:
        print(f"- First project: https://app.asana.com/0/{projects[0]['gid']}/list")
    
    print("\n✅ Done! Copy the IDs above for use in your GitHub workflow.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
