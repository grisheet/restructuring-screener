from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.event import Event
from app.models.score import Score
from app.services.scoring import compute_scores

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    company_id: int
    event_type: str
    description: str | None = None
    severity: float = 5.0


class EventOut(BaseModel):
    id: int
    company_id: int
    event_type: str
    description: str | None
    severity: float

    class Config:
        from_attributes = True


@router.get("/", response_model=List[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(Event).all()


@router.post("/", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)

    # Recompute scores for the company
    scores = compute_scores(event.company_id, db)
    score_record = Score(
        company_id=event.company_id,
        distress_score=scores["distress_score"],
        restructuring_significance=scores["restructuring_significance"],
        turnaround_opportunity=scores["turnaround_opportunity"],
        explanation=scores["explanation"],
    )
    db.add(score_record)
    db.commit()

    return event
