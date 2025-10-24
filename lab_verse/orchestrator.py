import asyncio, logging, datetime
from lab_verse.agents import launch_swarm
from lab_verse.background_agent import agent_manager
from lab_verse.validators import compute_metrics
from lab_verse.prompts import render
from lab_verse.config import load_config, mutate_config
from lab_verse.cognition import MeaningSynth, prompt_enricher

logger = logging.getLogger("orchestrator")

class Orchestrator:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.mind = MeaningSynth(cfg.get("meaning_thresholds", {}))
        self.mind.load()          # warm start if state file exists
        self.loop_count = 0
        
        # Initialize background agents
        self._initialize_background_agents()

    def _initialize_background_agents(self):
        """Initialize background agents for Zapier integration"""
        try:
            # Create main orchestration agent
            self.orchestration_agent = agent_manager.create_agent("orchestration_agent")
            
            # Create content processing agent
            self.content_agent = agent_manager.create_agent("content_agent")
            
            # Create monitoring agent
            self.monitoring_agent = agent_manager.create_agent("monitoring_agent")
            
            logger.info("Background agents initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize background agents: {e}")

    async def cycle(self):
        logger.info("Loop %s", self.loop_count)
        
        # 1. run swarm
        swarm = await launch_swarm(self.cfg)
        trace = await swarm.run()
        
        # 2. validate
        outcomes = compute_metrics(trace)
        
        # 3. Trigger background agent workflows via Zapier
        await self._trigger_background_workflows(outcomes)
        
        # 4. cognition layer
        await self.mind.ingest(outcomes, {"loop": self.loop_count, "swarm_id": getattr(swarm, "id", "unknown")})
        new_concepts = await self.mind.conceptual_update()
        if new_concepts:
            logger.info("New concepts: %s", [c["concept"] for c in new_concepts])
            
            # Trigger Zapier workflow for new concepts
            await self._trigger_concept_workflow(new_concepts)
        
        # 5. evolve config
        enriched_vars = prompt_enricher.enrich(dict(self.cfg), self.mind.graph)
        new_cfg = mutate_config(enriched_vars, outcomes)
        self.cfg = new_cfg
        self.loop_count += 1
        self.mind.save()
        
        return outcomes

    async def _trigger_background_workflows(self, outcomes):
        """Trigger background agent workflows based on orchestration outcomes"""
        try:
            # Prepare tasks for different agents
            tasks = {
                "orchestration_agent": [{
                    "type": "orchestration_complete",
                    "outcomes": outcomes,
                    "loop_count": self.loop_count,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }],
                "content_agent": [{
                    "type": "content_generation",
                    "data": outcomes.get("content_data", {}),
                    "priority": "normal"
                }],
                "monitoring_agent": [{
                    "type": "alert",
                    "metrics": outcomes.get("metrics", {}),
                    "priority": "low"
                }]
            }
            
            # Run all agents
            results = await agent_manager.run_all_agents(tasks)
            
            logger.info(f"Background workflows triggered: {len(results)} agents")
            
        except Exception as e:
            logger.error(f"Failed to trigger background workflows: {e}")

    async def _trigger_concept_workflow(self, new_concepts):
        """Trigger Zapier workflow for new concepts discovered"""
        try:
            async with agent_manager.get_agent("content_agent") as agent:
                if agent:
                    await agent.trigger_zapier_workflow(
                        action="concept_discovery",
                        data={
                            "concepts": new_concepts,
                            "discovery_time": datetime.datetime.utcnow().isoformat(),
                            "loop_count": self.loop_count
                        },
                        priority="high"
                    )
                    logger.info(f"Concept discovery workflow triggered for {len(new_concepts)} concepts")
        except Exception as e:
            logger.error(f"Failed to trigger concept workflow: {e}")

    async def health_check(self):
        """Perform health check for the orchestrator and all agents"""
        try:
            # Check orchestrator health
            orchestrator_health = {
                "orchestrator": {
                    "status": "healthy",
                    "loop_count": self.loop_count,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            }
            
            # Check all background agents
            agents_health = await agent_manager.health_check_all()
            
            return {
                **orchestrator_health,
                "agents": agents_health
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "orchestrator": {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    async def main():
        orchestrator = Orchestrator({})
        await orchestrator.cycle()
    asyncio.run(main())