"""Event ORM model — represents a single restructuring catalyst."""
import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class EventType(str, enum.Enum):
    CHAPTER11 = "chapter11"
    CHAPTER15 = "chapter15"
    OUT_OF_COURT = "out_of_court"
    SPIN_OFF = "spin_off"
    ASSET_SALE = "asset_sale"
    DEBT_RESTRUCTURING = "debt_restructuring"
    LME = "lme"  # Liability Management Exercise
    STRATEGIC_REVIEW = "strategic_review"
    COVENANT_BREACH = "covenant_breach"
    GOING_CONCERN = "going_concern"
    MANAGEMENT_CHANGE = "management_change"
    ACTIVIST_CAMPAIGN = "activist_campaign"
    DISTRESSED_FINANCING = "distressed_financing"
    MERGER = "merger"
    OTHER = "other"


class EventStatus(str, enum.Enum):
    RUMORED = "rumored"
    ANNOUNCED = "announced"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)  # Deduplication key
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    event_type = Column(Enum(EventType), nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.ANNOUNCED)
    headline = Column(String(500))
    description = Column(Text)
    source = Column(String(255))        # Data source identifier
    source_url = Column(String(1000))

    # Financial details
    deal_size = Column(Float)           # USD millions
    debt_amount = Column(Float)         # USD millions affected
    equity_impact = Column(Float)       # Estimated equity impact USD millions

    # Dates
    event_date = Column(DateTime(timezone=True), nullable=False)
    effective_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="events")

    def __repr__(self) -> str:
        return f"<Event id={self.id} type={self.event_type} company_id={self.company_id}>"
