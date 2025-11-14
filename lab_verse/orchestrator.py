import asyncio, logging, datetime
from lab_verse.agents import launch_swarm
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

    async def cycle(self):
        logger.info("Loop %s", self.loop_count)
        # 1. run swarm
        swarm = await launch_swarm(self.cfg)
        trace = await swarm.run()
        # 2. validate
        outcomes = compute_metrics(trace)
        # 3. cognition layer
        await self.mind.ingest(outcomes, {"loop": self.loop_count, "swarm_id": getattr(swarm, "id", "unknown")})
        new_concepts = await self.mind.conceptual_update()
        if new_concepts:
            logger.info("New concepts: %s", [c["concept"] for c in new_concepts])
        # 4. evolve config
        enriched_vars = prompt_enricher.enrich(dict(self.cfg), self.mind.graph)
        new_cfg = mutate_config(enriched_vars, outcomes)
        self.cfg = new_cfg
        self.loop_count += 1
        self.mind.save()
        return outcomes

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    async def main():
        orchestrator = Orchestrator({})
        await orchestrator.cycle()
    asyncio.run(main())