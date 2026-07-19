from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.score import Score

router = APIRouter(prefix="/scores", tags=["scores"])


class ScoreOut(BaseModel):
    id: int
    company_id: int
    distress_score: float
    restructuring_significance: float
    turnaround_opportunity: float
    explanation: dict

    class Config:
        from_attributes = True


@router.get("/{company_id}", response_model=ScoreOut)
def get_latest_score(company_id: int, db: Session = Depends(get_db)):
    score = (
        db.query(Score)
        .filter(Score.company_id == company_id)
        .order_by(Score.computed_at.desc())
        .first()
    )
    if not score:
        raise HTTPException(status_code=404, detail="No scores found for this company")
    return score


@router.get("/{company_id}/history", response_model=List[ScoreOut])
def get_score_history(company_id: int, db: Session = Depends(get_db)):
    scores = (
        db.query(Score)
        .filter(Score.company_id == company_id)
        .order_by(Score.computed_at.desc())
        .all()
    )
    return scores
