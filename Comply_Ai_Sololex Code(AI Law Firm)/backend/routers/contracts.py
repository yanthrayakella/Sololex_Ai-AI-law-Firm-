import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from agents.contract_updater import generate_updated_files
from auth_utils import get_current_user
from config import settings
from db import Contract, UpdatedContract, User, clauses_json_load, get_db
from schemas import ContractDetailResponse, ContractSummary, FixRequestBody
from services.document_parser import build_clauses_for_upload

router = APIRouter(prefix="/api/contracts", tags=["contracts"])

ALLOWED = {".pdf", ".docx", ".txt"}


@router.post("/upload", response_model=ContractDetailResponse)
async def upload_contract(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    contract_type: str = Form(...),
):
    ct = contract_type.lower().strip()
    if ct not in ("employment", "supplier", "lease", "service"):
        raise HTTPException(400, "Invalid contract type")

    suffix = Path(file.filename or "contract").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(400, "Only PDF, DOCX, or TXT are allowed")

    uid = str(uuid.uuid4())
    dest = settings.UPLOADS_DIR / f"{uid}{suffix}"
    content = await file.read()
    dest.write_bytes(content)

    clauses_json, risk = build_clauses_for_upload(dest, ct)
    contract = Contract(
        user_id=user.id,
        name=file.filename or dest.name,
        type=ct,
        file_path=str(dest),
        clauses_json=clauses_json,
        risk_score=risk,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract_detail(contract)


def contract_detail(c: Contract) -> ContractDetailResponse:
    return ContractDetailResponse(
        id=c.id,
        name=c.name,
        type=c.type,
        risk_score=c.risk_score,
        file_path=c.file_path,
        clauses=clauses_json_load(c.clauses_json),
        created_at=c.created_at,
    )


@router.get("", response_model=list[ContractSummary])
def list_contracts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Contract)
        .filter(Contract.user_id == user.id)
        .order_by(Contract.created_at.desc())
        .all()
    )
    return rows


@router.get("/updated/{updated_id}/download")
def download_updated(
    updated_id: str,
    fmt: str = "docx",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(UpdatedContract)
        .filter(UpdatedContract.id == updated_id, UpdatedContract.user_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(404, "Updated contract not found")
    base = Path(row.updated_file_path)
    if fmt.lower() == "pdf":
        path = base.with_suffix(".pdf")
    else:
        path = base
    if not path.is_file():
        raise HTTPException(404, "File missing")
    return FileResponse(path, filename=path.name)


@router.get("/{contract_id}", response_model=ContractDetailResponse)
def get_contract(contract_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.user_id == user.id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Contract not found")
    return contract_detail(c)


@router.get("/{contract_id}/file")
def download_original(contract_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.user_id == user.id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Contract not found")
    path = Path(c.file_path)
    if not path.is_file():
        raise HTTPException(404, "File missing")
    return FileResponse(path, filename=path.name)


@router.post("/{contract_id}/fix")
def fix_clause(
    contract_id: str,
    body: FixRequestBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.user_id == user.id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Contract not found")
    if body.apply_automatic and user.subscription_tier != "pro":
        raise HTTPException(403, "Automatic apply requires Pro subscription")
    try:
        row, docx_path, pdf_path = generate_updated_files(
            db, user, c, body.clause_id, body.apply_automatic
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "updated_id": row.id,
        "docx_path": docx_path,
        "pdf_path": pdf_path,
        "summary": row.changes_summary,
        "subscription_tier": user.subscription_tier,
    }
