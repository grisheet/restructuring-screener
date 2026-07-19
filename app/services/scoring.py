"""Scoring engine — computes Distress, Restructuring Significance, and Turnaround Opportunity scores.

All scores are 0-100. Higher Distress = more stressed. Higher Turnaround = more recoverable.
Designed to SEPARATE: a terminal Ch.11 scores high Distress / low Turnaround.
A stressed-but-alive LME candidate scores high on both.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional

from app.models.company import Company
from app.models.event import Event, EventType


# Event severity weights for restructuring significance scoring
EVENT_SEVERITY: dict[str, float] = {
    EventType.CHAPTER11: 1.0,
    EventType.CHAPTER15: 0.9,
    EventType.OUT_OF_COURT: 0.7,
    EventType.DEBT_RESTRUCTURING: 0.75,
    EventType.LME: 0.65,
    EventType.GOING_CONCERN: 0.6,
    EventType.COVENANT_BREACH: 0.5,
    EventType.STRATEGIC_REVIEW: 0.4,
    EventType.ASSET_SALE: 0.45,
    EventType.SPIN_OFF: 0.35,
    EventType.MANAGEMENT_CHANGE: 0.3,
    EventType.DISTRESSED_FINANCING: 0.55,
    EventType.ACTIVIST_CAMPAIGN: 0.4,
    EventType.MERGER: 0.3,
    EventType.OTHER: 0.2,
}


@dataclass
class ScoreResult:
    distress_score: float
    restructuring_significance: float
    turnaround_opportunity: float
    distress_breakdown: dict = field(default_factory=dict)
    restructuring_breakdown: dict = field(default_factory=dict)
    turnaround_breakdown: dict = field(default_factory=dict)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _sigmoid(x: float, midpoint: float = 5.0, steepness: float = 0.5) -> float:
    """Smooth 0-1 sigmoid used for leverage scoring."""
    return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))


def compute_distress_score(company: Company, events: list[Event]) -> tuple[float, dict]:
    """Compute 0-100 distress score with per-factor breakdown."""
    breakdown: dict[str, float] = {}

    # --- Leverage component (40% weight) ---
    leverage_score = 0.0
    if company.leverage_ratio is not None:
        # Net Debt/EBITDA: 0 = 0, 3 = ~50, 6+ = ~90
        leverage_score = _sigmoid(company.leverage_ratio, midpoint=4.0, steepness=0.6) * 90
    breakdown["leverage"] = round(leverage_score, 2)

    # --- Liquidity component (25% weight) ---
    liquidity_score = 0.0
    if company.cash is not None and company.total_debt is not None and company.total_debt > 0:
        cash_to_debt = company.cash / company.total_debt
        # Low cash relative to debt = high distress
        liquidity_score = max(0, (1 - cash_to_debt) * 100)
        liquidity_score = _clamp(liquidity_score)
    breakdown["liquidity"] = round(liquidity_score, 2)

    # --- Event-driven component (35% weight) ---
    event_score = 0.0
    high_severity_events = [
        e for e in events if e.event_type in (
            EventType.CHAPTER11, EventType.CHAPTER15, EventType.GOING_CONCERN, EventType.COVENANT_BREACH
        )
    ]
    if high_severity_events:
        # Each high-severity event adds significantly to distress
        event_score = min(100, len(high_severity_events) * 25 + 50)
    elif events:
        # Other events add moderate distress
        event_score = min(60, len(events) * 10)
    breakdown["event_severity"] = round(event_score, 2)

    # Weighted combination
    distress = (leverage_score * 0.40) + (liquidity_score * 0.25) + (event_score * 0.35)
    return _clamp(distress), breakdown


def compute_restructuring_significance(events: list[Event]) -> tuple[float, dict]:
    """Compute 0-100 restructuring significance score."""
    breakdown: dict[str, float] = {}

    if not events:
        return 0.0, {"severity": 0.0, "breadth": 0.0, "creditor_impact": 0.0}

    # --- Severity: max severity of any event ---
    max_severity = max(EVENT_SEVERITY.get(e.event_type, 0.2) for e in events)
    severity_score = max_severity * 100
    breakdown["severity"] = round(severity_score, 2)

    # --- Breadth: how many distinct event types ---
    unique_types = len({e.event_type for e in events})
    breadth_score = min(100, unique_types * 20)
    breakdown["breadth"] = round(breadth_score, 2)

    # --- Creditor impact: deal size weighted ---
    total_debt_impact = sum(e.debt_amount or 0.0 for e in events)
    creditor_score = min(100, total_debt_impact / 100)  # Scales at $10B = 100
    breakdown["creditor_impact"] = round(creditor_score, 2)

    significance = (severity_score * 0.5) + (breadth_score * 0.3) + (creditor_score * 0.2)
    return _clamp(significance), breakdown


def compute_turnaround_opportunity(company: Company, events: list[Event]) -> tuple[float, dict]:
    """Compute 0-100 turnaround opportunity score.

    The stabilization curve deliberately refuses to reward terminal situations.
    High distress AND no operational base = low turnaround.
    """
    breakdown: dict[str, float] = {}

    # Terminal events strongly suppress turnaround
    terminal_events = [e for e in events if e.event_type == EventType.CHAPTER11]
    if terminal_events:
        breakdown["stabilization"] = 5.0
        breakdown["mgmt_quality"] = 10.0
        breakdown["asset_coverage"] = 15.0
        return 6.0, breakdown

    # --- Stabilization: inverse of high-severity event count ---
    high_sev_count = sum(
        1 for e in events
        if EVENT_SEVERITY.get(e.event_type, 0.2) >= 0.6
    )
    stabilization = max(0, 80 - high_sev_count * 20)
    breakdown["stabilization"] = round(stabilization, 2)

    # --- Management quality signal: management change = positive signal ---
    mgmt_change_events = [e for e in events if e.event_type == EventType.MANAGEMENT_CHANGE]
    mgmt_quality = 50.0 + (len(mgmt_change_events) * 15)
    mgmt_quality = _clamp(mgmt_quality)
    breakdown["mgmt_quality"] = round(mgmt_quality, 2)

    # --- Asset coverage: enterprise value relative to total debt ---
    asset_coverage = 50.0
    if company.enterprise_value and company.total_debt and company.total_debt > 0:
        ev_to_debt = company.enterprise_value / company.total_debt
        asset_coverage = _clamp(ev_to_debt * 50)  # 2x coverage = 100
    breakdown["asset_coverage"] = round(asset_coverage, 2)

    turnaround = (stabilization * 0.4) + (mgmt_quality * 0.3) + (asset_coverage * 0.3)
    return _clamp(turnaround), breakdown


def compute_scores(company: Company, events: list[Event]) -> ScoreResult:
    """Compute all three scores for a company given its events."""
    distress, distress_breakdown = compute_distress_score(company, events)
    significance, restructuring_breakdown = compute_restructuring_significance(events)
    turnaround, turnaround_breakdown = compute_turnaround_opportunity(company, events)

    return ScoreResult(
        distress_score=round(distress, 2),
        restructuring_significance=round(significance, 2),
        turnaround_opportunity=round(turnaround, 2),
        distress_breakdown=distress_breakdown,
        restructuring_breakdown=restructuring_breakdown,
        turnaround_breakdown=turnaround_breakdown,
    )
