from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.company import Company
from app.models.score import Score
from app.services.scoring import compute_scores

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyCreate(BaseModel):
    name: str
    ticker: str | None = None
    sector: str | None = None


class ScoreOut(BaseModel):
    distress_score: float
    restructuring_significance: float
    turnaround_opportunity: float
    explanation: dict

    class Config:
        from_attributes = True


class CompanyOut(BaseModel):
    id: int
    name: str
    ticker: str | None
    sector: str | None
    latest_score: ScoreOut | None = None

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    result = []
    for c in companies:
        score = (
            db.query(Score)
            .filter(Score.company_id == c.id)
            .order_by(Score.computed_at.desc())
            .first()
        )
        result.append(
            CompanyOut(
                id=c.id,
                name=c.name,
                ticker=c.ticker,
                sector=c.sector,
                latest_score=ScoreOut(
                    distress_score=score.distress_score,
                    restructuring_significance=score.restructuring_significance,
                    turnaround_opportunity=score.turnaround_opportunity,
                    explanation=score.explanation or {},
                )
                if score
                else None,
            )
        )
    return result


@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return CompanyOut(id=company.id, name=company.name, ticker=company.ticker, sector=company.sector)


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    score = (
        db.query(Score)
        .filter(Score.company_id == company_id)
        .order_by(Score.computed_at.desc())
        .first()
    )
    return CompanyOut(
        id=company.id,
        name=company.name,
        ticker=company.ticker,
        sector=company.sector,
        latest_score=ScoreOut(
            distress_score=score.distress_score,
            restructuring_significance=score.restructuring_significance,
            turnaround_opportunity=score.turnaround_opportunity,
            explanation=score.explanation or {},
        )
        if score
        else None,
    )
