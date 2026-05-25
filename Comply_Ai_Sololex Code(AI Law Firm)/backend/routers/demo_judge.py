"""Public judge demo — no authentication."""

import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from services.work_permit_demo import (
    DEMO_DIR,
    FAKE_REGULATION_BODY,
    FAKE_REGULATION_TITLE,
    SAMPLE_WORK_PERMIT,
    apply_fake_update,
    ensure_demo_dir,
    save_upload,
)

router = APIRouter(prefix="/api/demo", tags=["judge-demo"])


@router.get("/regulation")
def regulation_sample():
    return JSONResponse(
        {
            "title": FAKE_REGULATION_TITLE,
            "effective_date": "March 28, 2026",
            "body": FAKE_REGULATION_BODY,
            "disclaimer": "This update is fabricated for courtroom / demonstration purposes only.",
        }
    )


@router.get("/sample-work-permit")
def download_sample_work_permit():
    return PlainTextResponse(
        SAMPLE_WORK_PERMIT,
        headers={
            "Content-Disposition": 'attachment; filename="sample-work-permit-demo.txt"',
        },
        media_type="text/plain; charset=utf-8",
    )


@router.post("/upload")
async def demo_upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "permit").suffix.lower()
    if suffix not in ALLOWED:
        raise HTTPException(
            400,
            detail="Please upload a .txt, .docx, or .pdf work permit document.",
        )
    session_id = str(uuid.uuid4())
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(400, detail="File too large (max 15 MB).")
    try:
        save_upload(session_id, content, suffix)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    return {
        "session_id": session_id,
        "filename": file.filename or f"upload{suffix}",
    }


@router.post("/{session_id}/apply-update")
def demo_apply_update(session_id: str):
    try:
        path, filename = apply_fake_update(session_id)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    return {"ok": True, "filename": filename, "session_id": session_id}


@router.get("/{session_id}/download/updated")
def demo_download_updated(session_id: str):
    try:
        ensure_demo_dir(session_id)
        d = DEMO_DIR / session_id
        for ext in (".pdf", ".docx", ".txt"):
            p = d / f"updated_work_permit{ext}"
            if p.is_file():
                return FileResponse(
                    p,
                    filename=f"updated-work-permit-demo{ext}",
                    media_type="application/octet-stream",
                )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
    raise HTTPException(404, detail="Updated file not found. Run apply-update first.")
