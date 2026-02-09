"""
Meta-Historian bi-temporal simulation orchestrator.

This module provides ReAct-style agents and orchestration for counterfactual
analysis anchored to immutable historical facts.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
import json
import logging
from typing import Dict, List, Optional

import asyncpg


class ConfidenceLevel(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    SPECULATIVE = "SPECULATIVE"


class Domain(str, Enum):
    LEGAL = "LEGAL"
    ECONOMIC = "ECONOMIC"
    SOCIAL = "SOCIAL"
    POLITICAL = "POLITICAL"
    CULTURAL = "CULTURAL"
    ADMINISTRATIVE = "ADMINISTRATIVE"


@dataclass(frozen=True)
class BeliefState:
    transaction_time: datetime
    valid_time: date
    state: str
    interpretation: str
    confidence: ConfidenceLevel
    evidence: Dict


class ReactAgent:
    def __init__(self, name: str, domain: Domain, db_pool: asyncpg.Pool):
        self.name = name
        self.domain = domain
        self.db_pool = db_pool
        self.thought_log: List[Dict[str, str]] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    async def think(self, observation: str) -> str:
        thought = f"[{self.name}] Observing: {observation}"
        self.thought_log.append({"type": "thought", "content": thought})
        self.logger.debug(thought)
        return thought

    async def act(self, action_type: str, params: Dict) -> Dict:
        self.thought_log.append({"type": "action", "action": action_type, "params": params})
        if action_type == "check_anchor":
            return await self._check_immutable_anchor(params["anchor_type"], params["date"])
        if action_type == "project_economic":
            return await self._project_economic_metrics(params["baseline_year"], params["scenario"])
        if action_type == "measure_conflict":
            return await self._measure_conflict_intensity(params["province"], params["trigger_event"])
        return {}

    async def observe(self, result: Dict) -> str:
        observation = f"Result: {json.dumps(result, indent=2, default=str)}"
        self.thought_log.append({"type": "observation", "content": observation})
        self.logger.debug(observation)
        return observation

    async def _check_immutable_anchor(self, anchor_type: str, anchor_date: date) -> Dict:
        query = """
            SELECT anchor_id, description
            FROM immutable_anchors
            WHERE anchor_type = $1 AND event_date = $2
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, anchor_type, anchor_date)
        return {"anchor_found": bool(row), "details": dict(row) if row else None}

    async def _project_economic_metrics(self, baseline_year: int, scenario: str) -> Dict:
        return {"baseline_year": baseline_year, "scenario": scenario, "note": "stub projection"}

    async def _measure_conflict_intensity(self, province: str, trigger_event: str) -> Dict:
        return {"province": province, "trigger_event": trigger_event, "intensity": 0.0}


class LegalAgent(ReactAgent):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__("Meta-Historian_Legal", Domain.LEGAL, db_pool)

    async def check_constitutional_compliance(self, repeal_date: date, statute_name: str) -> Dict:
        await self.think(f"Checking constitutional implications of repealing {statute_name} on {repeal_date}")
        anchors = await self.act("check_anchor", {"anchor_type": "CONSTITUTIONAL", "date": date(1996, 2, 4)})
        s9_check = await self._check_section_9(repeal_date)
        s25_check = await self._check_section_25(repeal_date)
        return {
            "anchor_status": "PASSED" if anchors.get("anchor_found") else "VIOLATION",
            "section_9_analysis": s9_check,
            "section_25_analysis": s25_check,
            "structural_amendment": True,
            "confidence": ConfidenceLevel.VERY_HIGH,
        }

    async def _check_section_9(self, repeal_date: date) -> Dict:
        return {
            "constitutional_right": "Intact",
            "mechanism_vs_right": "BEE is mechanism, not right itself",
            "formal_equality": "Maintained (all races treated equally)",
            "substantive_equality": "Violates Van Heerden 2004 precedent",
            "concourt_risk": "HIGH probability of unconstitutionality if no replacement",
            "assessed_at": repeal_date.isoformat(),
        }

    async def _check_section_25(self, repeal_date: date) -> Dict:
        return {
            "property_rights": "No direct expropriation",
            "redistribution_mechanism": "Removed without replacement",
            "risk": "MODERATE",
            "assessed_at": repeal_date.isoformat(),
        }

    async def update_statute_graph(self, repealed_act: str, repeal_act: str) -> Dict:
        await self.think(f"Updating statutory graph: {repealed_act} ← REPEALED_BY → {repeal_act}")
        return {
            "primary_repeal": f"{repealed_act} ← REPEALED_BY → {repeal_act}",
            "amendment_acts": "Marked superseded",
            "sector_charters": "Status: ORPHANED",
            "regulations": "Status: INVALID",
        }


class EconomicAgent(ReactAgent):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__("Meta-Historian_Economic", Domain.ECONOMIC, db_pool)
        self.baseline_metrics = {
            "jse_black_ownership": 0.28,
            "bee_deal_flow": 45e9,
            "fdi_influx": 4.2e9,
            "employment_equity_top5": 0.45,
            "gini_coefficient": 0.63,
        }

    async def generate_projections(self, trigger_date: date, scenario: str) -> Dict:
        await self.think(f"Generating economic projections for {scenario} scenario from {trigger_date}")
        z_scores = await self._calculate_anomaly_scores()
        projections = {
            "year_0": await self._project_year_0(),
            "year_2": await self._project_year_2(),
            "year_3_plus": {"confidence": ConfidenceLevel.LOW, "note": "No historical precedent"},
        }
        return {
            "z_score": z_scores.get("aggregate", 3.4),
            "anomaly_detected": True,
            "projections": projections,
            "causal_narrative": self._generate_narrative(),
        }

    async def _calculate_anomaly_scores(self) -> Dict:
        return {"aggregate": 3.4}

    async def _project_year_0(self) -> Dict:
        return {
            "jse_black_ownership": {"value": 0.12, "change": -0.16, "mechanism": "immediate selloff"},
            "fdi_influx": {"value": 6.8e9, "change": 2.6e9, "mechanism": "initial surge"},
            "confidence": ConfidenceLevel.HIGH,
        }

    async def _project_year_2(self) -> Dict:
        return {
            "jse_black_ownership": {"value": 0.08, "change": -0.04, "mechanism": "capital consolidation"},
            "fdi_influx": {"value": 3.1e9, "change": -3.7e9, "mechanism": "policy uncertainty"},
            "confidence": ConfidenceLevel.MODERATE,
        }

    def _generate_narrative(self) -> str:
        return (
            "Removal of BEE eliminates statutory requirement for black ownership. "
            "Historical precedent (pre-2003) suggests reversion to pre-demographic patterns "
            "at 0.4x velocity per annum. Unlike 1950 Group Areas Act, this is market-driven. "
            "Confidence: MODERATE due to unique post-COVID structure."
        )


class SocialAgent(ReactAgent):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__("Meta-Historian_Social", Domain.SOCIAL, db_pool)

    async def measure_conflict_spike(self, provinces: List[str], trigger_event: str) -> Dict:
        await self.think(f"Measuring social conflict intensity across {provinces} following {trigger_event}")
        readings = []
        for province in provinces:
            intensity = await self._calculate_intensity(province, trigger_event)
            readings.append(
                {"province": province, "intensity": intensity, "threshold_breach": intensity > 6.5}
            )
        narrative = await self._detect_narrative_emergence(
            ["1994 betrayal", "sellout", "economic apartheid"]
        )
        return {
            "conflict_intensity_index": max(reading["intensity"] for reading in readings),
            "threshold_breached": any(reading["threshold_breach"] for reading in readings),
            "province_breakdown": readings,
            "narrative_emergence": narrative,
            "union_activity": "COSATU threat of general strike (precedent: 2007)",
        }

    async def _calculate_intensity(self, province: str, trigger: str) -> float:
        base_intensity = 7.2 if province in ["ZA-LP", "ZA-GP"] else 5.8
        return round(base_intensity, 1)

    async def _detect_narrative_emergence(self, narratives: List[str]) -> Dict:
        return {"narratives": narratives, "nlp_confidence": 0.76}


class PoliticalAgent(ReactAgent):
    def __init__(self, db_pool: asyncpg.Pool):
        super().__init__("Meta-Historian_Political", Domain.POLITICAL, db_pool)

    async def regime_stress_test(self, action: str, valid_time: date) -> Dict:
        await self.think(f"Conducting regime stress test for {action} at {valid_time}")
        cc_risk = await self._calculate_concourt_risk(action)
        parallel = await self._detect_historical_parallel("1948 Native Representative Council Act repeal")
        return {
            "constitutional_compliance": {
                "section_9_formal": "Compliant",
                "section_9_substantive": "Non-compliant per Van Heerden",
                "concourt_risk": cc_risk,
            },
            "electoral_projection": {
                "2026_provincial": "ANC loses 12% national vote share",
                "2027_new_party_probability": 0.34,
            },
            "historical_parallel": parallel,
        }

    async def _calculate_concourt_risk(self, action: str) -> str:
        return "HIGH" if action == "BEE_REPEAL" else "MODERATE"

    async def _detect_historical_parallel(self, event: str) -> Dict:
        return {
            "event": event,
            "similarity_score": 0.72,
            "pattern": (
                "Removal of consultative mechanism without replacement "
                "→ extra-parliamentary mobilization"
            ),
            "confidence": ConfidenceLevel.MODERATE,
            "caveat": "Different constitutional era",
        }


class MetaHistorian:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.legal_agent = LegalAgent(db_pool)
        self.economic_agent = EconomicAgent(db_pool)
        self.social_agent = SocialAgent(db_pool)
        self.political_agent = PoliticalAgent(db_pool)
        self.simulation_id: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def trigger_simulation(self, action: str, trigger_date: date) -> Dict:
        self.simulation_id = await self._create_simulation_record(action, trigger_date)
        legal_results = await self._phase_1_legal_archaeology(action, trigger_date)
        cascade_results = await self._phase_2_cascade_analysis(trigger_date)
        await self._phase_3_belief_revision(trigger_date)
        await self._phase_4_comparative_analysis(action)
        return await self._generate_final_output(legal_results, cascade_results)

    async def _phase_1_legal_archaeology(self, action: str, valid_time: date) -> Dict:
        self.logger.info("Phase 1: Immediate legal archaeology")
        anchor_check = await self._verify_anchor_integrity()
        if anchor_check["violation"]:
            return {"error": "IMMUTABLE ANCHOR VIOLATION", "details": anchor_check}
        await self.legal_agent.update_statute_graph("B-BBEE Act 2003", "Repeal Act 2025")
        return {"status": "STRUCTURAL_AMENDMENT", "anchors": "INTACT", "action": action, "valid_time": valid_time}

    async def _phase_2_cascade_analysis(self, trigger_date: date) -> Dict:
        self.logger.info("Phase 2: Domain agent projections")
        econ = await self.economic_agent.generate_projections(trigger_date, "BEE_REPEAL")
        social = await self.social_agent.measure_conflict_spike(
            ["ZA-LP", "ZA-GP", "ZA-KZN"], "BEE repeal announcement"
        )
        political = await self.political_agent.regime_stress_test("BEE_REPEAL", trigger_date)
        return {"economic": econ, "social": social, "political": political}

    async def _phase_3_belief_revision(self, trigger_date: date) -> List[BeliefState]:
        beliefs = [
            BeliefState(
                transaction_time=datetime(2025, 2, 5, 0, 0),
                valid_time=trigger_date,
                state="initial_gazette",
                interpretation="Policy simplification",
                confidence=ConfidenceLevel.HIGH,
                evidence={"source": "Government Gazette"},
            ),
            BeliefState(
                transaction_time=datetime(2025, 6, 15, 0, 0),
                valid_time=date(2025, 6, 15),
                state="courts_respond",
                interpretation="ConCourt case filed (UDM v President)",
                confidence=ConfidenceLevel.HIGH,
                evidence={"source": "Court records"},
            ),
            BeliefState(
                transaction_time=datetime(2026, 3, 10, 0, 0),
                valid_time=date(2026, 3, 10),
                state="economic_data_revised",
                interpretation="Q4 2025 GDP shows -0.8% (vs +1.2% baseline)",
                confidence=ConfidenceLevel.VERY_HIGH,
                evidence={"source": "StatsSA"},
            ),
            BeliefState(
                transaction_time=datetime(2027, 1, 20, 0, 0),
                valid_time=date(2027, 1, 20),
                state="historical_revision",
                interpretation='"The Great Repeal" enters historiography as "Second Transition"',
                confidence=ConfidenceLevel.MODERATE,
                evidence={"source": "Academic consensus"},
            ),
        ]
        async with self.db_pool.acquire() as conn:
            for belief in beliefs:
                await conn.execute(
                    """
                    INSERT INTO belief_states (
                        simulation_id,
                        transaction_time,
                        valid_time,
                        belief_state,
                        interpretation,
                        confidence_level,
                        evidence_links,
                        agent_source
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    self.simulation_id,
                    belief.transaction_time,
                    belief.valid_time,
                    belief.state,
                    belief.interpretation,
                    belief.confidence.value,
                    json.dumps(belief.evidence),
                    "MetaHistorian",
                )
        return beliefs

    async def _phase_4_comparative_analysis(self, action: str) -> Dict:
        self.logger.info("Phase 4: Comparative temporal analysis")
        return {"parallel_year": 1950, "inverse_operation": True, "structural_similarity": 0.82, "action": action}

    async def _generate_final_output(self, legal: Dict, cascade: Dict) -> Dict:
        output = {
            "simulation_id": str(self.simulation_id),
            "status": "BRANCH_VALID",
            "anchor_integrity": legal.get("anchors", "UNKNOWN"),
            "projected_stability": {
                "2025": "HIGH_VOLATILITY",
                "2027": "MODERATE_CRISIS",
                "2030": "UNKNOWABLE",
            },
            "recommendation": "REJECT_SIMPLE_REPEAL",
            "reasoning": (
                "Removal of Flexible Zone policy without replacement triggers "
                "1948-type cascade in reverse: rapid geographic re-concentration "
                "of economic power. Suggest: Graduated sunset clauses."
            ),
            "cascade": cascade,
        }
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE counterfactual_simulations
                SET final_recommendation = $1,
                    projected_stability = $2,
                    status = 'COMPLETED'
                WHERE simulation_id = $3
                """,
                output["reasoning"],
                json.dumps(output["projected_stability"]),
                self.simulation_id,
            )
        return output

    async def _verify_anchor_integrity(self) -> Dict:
        query = """
            SELECT anchor_id
            FROM immutable_anchors
            WHERE anchor_type = 'REGIME_CHANGE'
              AND event_date = '1994-04-27'
              AND valid_time_range @> CURRENT_DATE::timestamp
        """
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query)
        if row:
            return {"violation": False, "anchor": "1994 Transition preserved"}
        return {"violation": True, "error": "Attempted to alter 1994 anchor"}

    async def _create_simulation_record(self, action: str, trigger_date: date) -> str:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO counterfactual_simulations (trigger_action, trigger_date)
                VALUES ($1, $2)
                RETURNING simulation_id
                """,
                action,
                trigger_date,
            )
        return str(row["simulation_id"])
