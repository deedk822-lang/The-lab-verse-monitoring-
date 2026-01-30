import asyncio
import json
import logging
import os
from typing import Any, Dict

import aiohttp
import openlit
import redis.asyncio as redis
import yaml
from openai import AsyncOpenAI

openlit.init()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CognitiveSwarmOrchestrator:
    """
    Listens for events, uses a Supervisor Agent to create a plan,
    and executes the plan with a swarm of specialized AI agents.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = redis.from_url(
            f"redis://{config['redis']['host']}:{config['redis']['port']}/{config['redis']['db']}",
            decode_responses=True,
        )
        # This client is configured via environment variables for security
        self.ai_client = AsyncOpenAI(timeout=config["ai_client"]["timeout"])
        self.agent_model_map = config["agent_model_map"]

    async def _send_slack_notification(self, message: str):
        """Sends a final report to a Slack webhook."""
        if not self.config["notifications"]["slack"]["enabled"]:
            return

        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("Slack notifications enabled, but SLACK_WEBHOOK_URL is not set.")
            return

        payload = {"text": message}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    response.raise_for_status()
            logger.info("Successfully sent report to Slack.")
        except aiohttp.ClientError as e:
            logger.error(f"Failed to send Slack notification: {e}")

    async def _run_supervisor_agent(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a strategic plan using the Supervisor Agent."""
        logger.info("Activating Supervisor Agent to generate plan...")

        prompt = f"""
        SYSTEM: You are a world-class AI strategist and task planner. Your role is to receive a raw data event and transform it into a high-level strategic question and a step-by-step execution plan for a swarm of specialized AI agents. The plan must be a valid JSON object.

        Available agent types: {list(self.agent_model_map.keys())}

        USER:
        Here is the incoming event payload:
        ```json
        {json.dumps(event_payload, indent=2)}
        ```

        Based on this event, generate a JSON object with two keys:
        1. `strategic_question`: A single, high-level question that captures the core strategic importance of this event.
        2. `execution_plan`: An array of task objects. Each object must have `step` (int), `goal` (str), and `agent_type` (str).

        Ensure the final step is always a `synthesis_reasoning` task. Respond with nothing but the raw JSON.
        """

        try:
            response = await self.ai_client.chat.completions.create(
                model=self.agent_model_map["supervisor"],
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            plan_str = response.choices[0].message.content
            logger.info(f"Supervisor Agent generated plan:\n{plan_str}")
            return json.loads(plan_str)
        except Exception as e:
            logger.error(f"Supervisor Agent failed: {e}")
            raise

    async def _execute_agent_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Executes a single step of the plan with a specialized agent."""
        agent_type = task["agent_type"]
        model = self.agent_model_map.get(agent_type)
        if not model:
            raise ValueError(f"Invalid agent_type: {agent_type}. No model mapped in config.")

        logger.info(
            f"Executing Step {task['step']} ('{task['goal']}') with Agent '{agent_type}' ({model})..."
        )

        # The context provides all prior results to the current agent
        prompt = f"""
        You are an AI agent of type '{agent_type}'. Your goal is: "{task["goal"]}".

        Here is the full context of the mission so far, including the strategic question and results from previous steps:
        ```json
        {json.dumps(context, indent=2)}
        ```

        Fulfill your goal. Provide a concise and direct response focusing only on your specific task.
        """

        try:
            response = await self.ai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            result = response.choices[0].message.content
            logger.info(f"Step {task['step']} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Agent '{agent_type}' failed on Step {task['step']}: {e}")
            return f"ERROR: Agent '{agent_type}' failed. Reason: {e}"

    async def _handle_event(self, event_message: str):
        """Main workflow for handling a single event from start to finish."""
        try:
            event_payload = json.loads(event_message)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {event_message}")
            return

        try:
            plan_data = await self._run_supervisor_agent(event_payload)
        except Exception:
            logger.error("Failed to generate a plan. Aborting mission.")
            return

        context = {
            "original_event": event_payload,
            "strategic_question": plan_data.get("strategic_question"),
            "execution_plan": plan_data.get("execution_plan"),
            "step_results": {},
        }

        # Execute plan steps sequentially
        for task in sorted(context["execution_plan"], key=lambda x: x["step"]):
            step_result = await self._execute_agent_task(task, context)
            context["step_results"][f"step_{task['step']}"] = {
                "goal": task["goal"],
                "result": step_result,
            }

        final_report = f"""
        **Cognitive Swarm Mission Report**
        --------------------------------------
        **Strategic Question:** {context["strategic_question"]}
        --------------------------------------

        **Final Analysis & Recommendation:**
        {context["step_results"][f"step_{len(context["execution_plan"])}"]["result"]}

        ---
        *Source Event: {context["original_event"]["source"]} - {context["original_event"]["event_type"]}*
        """

        logger.info("Mission complete. Final report generated.")
        print("--- FINAL REPORT ---")
        print(final_report)
        print("--------------------")

        await self._send_slack_notification(final_report)

    async def listen_for_events(self):
        """Connects to Redis and listens for events to trigger the swarm."""
        logger.info("Cognitive Swarm Orchestrator is online. Listening for events...")
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(self.config["redis"]["events_channel"])

        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60)
                if message:
                    logger.info(
                        f"Received event on channel '{message['channel']}'. Triggering swarm..."
                    )
                    # Run handler in the background to not block the listener
                    asyncio.create_task(self._handle_event(message["data"]))
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event listener loop: {e}")
                await asyncio.sleep(5)  # Avoid rapid-fire errors


async def main():
    # Load configuration
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # Initialize services
    redis_client = redis.from_url(
        f"redis://{config['redis']['host']}:{config['redis']['port']}/{config['redis']['db']}"
    )

    # Create orchestrator and sensor
    orchestrator = CognitiveSwarmOrchestrator(config)
    github_sensor = GitHubMonitorSensor(config, redis_client)

    # Run services concurrently
    logger.info("Starting all services...")
    await asyncio.gather(orchestrator.listen_for_events(), github_sensor.run())


if __name__ == "__main__":
    # Ensure required environment variables are set
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("OPENAI_API_BASE"):
        logger.error(
            "FATAL: OPENAI_API_KEY and OPENAI_API_BASE must be set as environment variables."
        )
        exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down services.")
