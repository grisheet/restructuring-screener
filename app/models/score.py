"""Score ORM model — versioned, materialized company scores."""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class Score(Base):
    """Materialized score snapshot for a company at a point in time.

    Scores are stored, not just computed on-the-fly, enabling:
    - Reproducible backtesting
    - Historical drift analysis
    - Efficient screening without recomputation
    """
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Primary scores (0-100)
    distress_score = Column(Float, nullable=False, default=0.0)
    restructuring_significance = Column(Float, nullable=False, default=0.0)
    turnaround_opportunity = Column(Float, nullable=False, default=0.0)

    # Score breakdowns (JSON factor-level detail for explainability)
    distress_breakdown = Column(JSON)           # {leverage: x, liquidity: y, covenant: z, ...}
    restructuring_breakdown = Column(JSON)      # {severity: x, breadth: y, creditor_impact: z}
    turnaround_breakdown = Column(JSON)         # {stabilization: x, mgmt_quality: y, asset_coverage: z}

    # Triggering event (which ingestion caused this recomputation)
    trigger_event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    company = relationship("Company", back_populates="scores")

    def __repr__(self) -> str:
        return (
            f"<Score company_id={self.company_id} "
            f"distress={self.distress_score:.1f} "
            f"restructuring={self.restructuring_significance:.1f} "
            f"turnaround={self.turnaround_opportunity:.1f}>"
        )
