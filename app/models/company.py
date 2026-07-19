"""Company ORM model."""
from sqlalchemy import Column, String, Float, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    country = Column(String(100))
    description = Column(Text)

    # Fundamentals (enrich-only: thin-payload sources cannot overwrite established values)
    total_debt = Column(Float)          # USD millions
    ebitda = Column(Float)              # USD millions
    cash = Column(Float)               # USD millions
    revenue = Column(Float)             # USD millions
    net_income = Column(Float)          # USD millions
    market_cap = Column(Float)          # USD millions
    enterprise_value = Column(Float)    # USD millions

    # Derived ratios (computed at ingestion)
    leverage_ratio = Column(Float)      # Net Debt / EBITDA
    interest_coverage = Column(Float)   # EBIT / Interest Expense

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    events = relationship("Event", back_populates="company", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="company", cascade="all, delete-orphan")
    watchlist_entries = relationship("WatchlistCompany", back_populates="company")

    def __repr__(self) -> str:
        return f"<Company ticker={self.ticker} name={self.name}>"
