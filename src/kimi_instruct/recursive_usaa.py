from .mcp.mcp_core import MCPCore
from .embodied.sandbox_runner import SandboxRunner
from .ethics.policy_gate import PolicyGate
from .ethics.multiobj_reward import MultiObjReward

class RecursiveUSAA:
    def __init__(self, base_service):
        self.base   = base_service
        self.mcp    = MCPCore(base_service)
        self.sandbox= SandboxRunner(base_service)
        self.gate   = PolicyGate(base_service)
        self.reward = MultiObjReward(base_service)

    async def run_recursive(self, goal: str, ctx: dict) -> dict:
        # ① MCL/MCP – critique & refine
        plan      = await self.base.run_usaa_goal(goal, ctx)
        refined, _ = await self.mcp.validate_and_refine(goal, plan, ctx)

        # ② EFL – sandbox execution (dry-run default)
        sandbox_results = await self.sandbox.run_plan(refined, dry_run=ctx.get("dry_run", True))
        metrics = {"success": all(s.get("ok", False) for s in sandbox_results), "risk": 0.1}

        # ③ EOL – ethics gate + reward
        ok, violations = self.gate.check(metrics)
        if not ok:
            return {"status": "halted", "violations": violations, "cost": 0.0}

        reward = self.reward.score(metrics)

        # ④ Forward to real USAA if safe
        if ctx.get("dry_run_only"):
            return {"status": "sandbox_ok", "reward": reward, "cost": 0.0}

        return await self.base.run_usaa_goal(goal, {**ctx, "refined_plan": refined})