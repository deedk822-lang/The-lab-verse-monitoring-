import asyncio
import aiohttp
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

logger = logging.getLogger("background_agent")

class BackgroundAgent:
    """Enhanced background agent with Zapier integration capabilities"""
    
    def __init__(self, agent_id: str, webhook_url: str = None):
        self.agent_id = agent_id
        self.webhook_url = webhook_url or os.getenv('ZAPIER_WEBHOOK_URL')
        self.session = None
        self.retry_count = 3
        self.retry_delay = 1  # seconds
        
        if not self.webhook_url:
            logger.warning(f"Agent {agent_id}: No Zapier webhook URL configured")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def trigger_zapier_workflow(self, action: str, data: Dict[Any, Any], 
                                    priority: str = "normal", 
                                    custom_webhook_url: str = None) -> Optional[Dict]:
        """Trigger a Zapier workflow from background agent with retry logic"""
        
        webhook_url = custom_webhook_url or self.webhook_url
        if not webhook_url:
            logger.error(f"Agent {self.agent_id}: No webhook URL available")
            return None

        payload = {
            "agent_id": self.agent_id,
            "action": action,
            "data": data,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "background_agent",
            "metadata": {
                "processing_time": asyncio.get_event_loop().time(),
                "agent_version": os.getenv('AGENT_VERSION', '1.0.0'),
                "server": os.getenv('SERVER_NAME', 'lab-verse')
            }
        }

        for attempt in range(self.retry_count):
            try:
                async with self.session.post(
                    webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Lab-Verse-Background-Agent/1.0"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Agent {self.agent_id}: Zapier workflow triggered successfully: {action}")
                        return result
                    else:
                        logger.warning(f"Agent {self.agent_id}: Zapier webhook returned status {response.status}")
                        if attempt < self.retry_count - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        return None

            except Exception as e:
                logger.error(f"Agent {self.agent_id}: Error triggering Zapier workflow (attempt {attempt + 1}): {e}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return None

        return None

    async def process_and_trigger(self, task_data: Dict[Any, Any]) -> Dict[str, Any]:
        """Process task and trigger appropriate Zapier workflow"""
        
        logger.info(f"Agent {self.agent_id}: Processing task")
        
        # Your background processing logic here
        processed_data = await self.process_task(task_data)
        
        # Determine action based on processing results
        action = self._determine_action(processed_data)
        priority = processed_data.get("priority", "normal")
        
        # Trigger Zapier workflow
        zapier_result = await self.trigger_zapier_workflow(action, processed_data, priority)
        
        return {
            "agent_id": self.agent_id,
            "task_processed": True,
            "action_triggered": action,
            "zapier_result": zapier_result,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _determine_action(self, processed_data: Dict[Any, Any]) -> str:
        """Determine the appropriate Zapier action based on processed data"""
        
        if processed_data.get("requires_ai_processing"):
            return "ai_content_generation"
        elif processed_data.get("requires_notification"):
            return "send_notification"
        elif processed_data.get("requires_data_sync"):
            return "sync_data"
        elif processed_data.get("requires_alert"):
            return "send_alert"
        elif processed_data.get("requires_backup"):
            return "backup_data"
        else:
            return "general_processing"

    async def process_task(self, task_data: Dict[Any, Any]) -> Dict[Any, Any]:
        """Your background task processing logic - override this method"""
        
        # Example processing logic
        processed_data = {
            **task_data,
            "processed_at": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id
        }
        
        # Add processing flags based on task type
        task_type = task_data.get("type", "unknown")
        
        if task_type == "content_generation":
            processed_data["requires_ai_processing"] = True
            processed_data["priority"] = "high"
        elif task_type == "notification":
            processed_data["requires_notification"] = True
            processed_data["priority"] = "normal"
        elif task_type == "data_sync":
            processed_data["requires_data_sync"] = True
            processed_data["priority"] = "low"
        elif task_type == "alert":
            processed_data["requires_alert"] = True
            processed_data["priority"] = "urgent"
        
        return processed_data

    async def batch_process_and_trigger(self, tasks: List[Dict[Any, Any]]) -> List[Dict[str, Any]]:
        """Process multiple tasks and trigger Zapier workflows"""
        
        results = []
        
        for task in tasks:
            try:
                result = await self.process_and_trigger(task)
                results.append(result)
            except Exception as e:
                logger.error(f"Agent {self.agent_id}: Error processing task: {e}")
                results.append({
                    "agent_id": self.agent_id,
                    "task_processed": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return results

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check for the background agent"""
        
        return {
            "agent_id": self.agent_id,
            "status": "healthy",
            "webhook_configured": bool(self.webhook_url),
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv('AGENT_VERSION', '1.0.0')
        }


class BackgroundAgentManager:
    """Manager for multiple background agents"""
    
    def __init__(self):
        self.agents: Dict[str, BackgroundAgent] = {}
        self.webhook_url = os.getenv('ZAPIER_WEBHOOK_URL')
    
    def create_agent(self, agent_id: str, webhook_url: str = None) -> BackgroundAgent:
        """Create a new background agent"""
        
        agent = BackgroundAgent(agent_id, webhook_url or self.webhook_url)
        self.agents[agent_id] = agent
        logger.info(f"Created background agent: {agent_id}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BackgroundAgent]:
        """Get an existing background agent"""
        return self.agents.get(agent_id)
    
    async def run_all_agents(self, tasks: Dict[str, List[Dict[Any, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Run all agents with their respective tasks"""
        
        results = {}
        
        for agent_id, agent_tasks in tasks.items():
            agent = self.get_agent(agent_id)
            if agent:
                async with agent:
                    results[agent_id] = await agent.batch_process_and_trigger(agent_tasks)
            else:
                logger.warning(f"Agent {agent_id} not found")
                results[agent_id] = []
        
        return results
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check for all agents"""
        
        results = {}
        
        for agent_id, agent in self.agents.items():
            async with agent:
                results[agent_id] = await agent.health_check()
        
        return results


# Global agent manager instance
agent_manager = BackgroundAgentManager()