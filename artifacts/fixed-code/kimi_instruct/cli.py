async def task_command(self, args):
    """Create and execute a task"""
    if not args.title:
        print("Error: --title required for task command")
        return

    # Parse priority
    try:
        priority = TaskPriority(args.priority)
    except ValueError:
        print(
            f"Error: Invalid priority '{args.priority}'. Use: low, medium, high, critical"
        )
        return

    # Create task
    if args.execute:
        print("\n🔄 Executing task...")
        success = await self.kimi.execute_task(args.id)
    else:
        print("Creating task without execution")

    if success:
        print(f"✅ Created task: {args.title}")
        print(f"   Title: {args.title}")
        print(f"   Priority: {priority.value}")
        print(f"   Status: {self.kimi.tasks[args.id].status.value}")

        # Execute immediately after creation
        if args.execute:
            success = await self.kimi.execute_task(args.id)
            if success:
                print("✅ Task executed successfully")
            else:
                print("❌ Task execution failed")

    else:
        print("❌ Failed to create task")