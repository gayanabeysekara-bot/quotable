from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..deps import OrgContext, require
from ..models import EvaluationRun
from ..permissions import Perm
from ..schemas import EvaluationIn, EvaluationOut

router = APIRouter(prefix="/api/orgs/{org_id}/evaluations", tags=["evaluation"])


@router.get("", response_model=list[EvaluationOut])
def list_runs(ctx: OrgContext = Depends(require(Perm.VIEW)), db: Session = Depends(get_db)):
    return db.scalars(select(EvaluationRun).where(EvaluationRun.org_id == ctx.org_id)
                      .order_by(EvaluationRun.created_at.desc()).limit(200)).all()


@router.post("", response_model=EvaluationOut, status_code=201)
def submit_run(body: EvaluationIn, request: Request, ctx: OrgContext = Depends(require(Perm.RUN_EVALUATION)),
               db: Session = Depends(get_db)):
    """Store a report produced by `python -m evaluation.run` (evaluation/README.md)."""
    run = EvaluationRun(org_id=ctx.org_id, created_by=ctx.user.id, **body.model_dump())
    db.add(run)
    db.flush()
    audit.record(db, "evaluation.submitted", org_id=ctx.org_id, actor_user_id=ctx.user.id,
                 actor_label=ctx.user.email, target_type="evaluation", target_id=run.id, request=request,
                 details={"name": body.name, "model": body.model_name})
    db.commit()
    return run
