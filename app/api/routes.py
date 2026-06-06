from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.db import User
from app.dependencies.auth import get_current_user
from app.services.analyzer import analyze_workbook


router = APIRouter()


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/sample-status")
def sample_status(current_user: User = Depends(get_current_user)) -> dict[str, str | bool | None]:
    path = settings.sample_workbook_path
    return {
        "available": bool(path and Path(path).exists()),
        "path": path,
        "filename": os.path.basename(path) if path else None,
    }


@router.get("/analyze-sample")
def analyze_sample(current_user: User = Depends(get_current_user)) -> dict:
    path = settings.sample_workbook_path
    if not path or not Path(path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sample workbook is not configured or cannot be found.",
        )
    return analyze_workbook(path, os.path.basename(path))


@router.post("/analyze")
async def analyze_uploaded_workbook(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict:
    suffix = Path(file.filename or "uploaded-workbook.xlsx").suffix or ".xlsx"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_path = temp_file.name
        while chunk := await file.read(1024 * 1024):
            temp_file.write(chunk)

    try:
        return analyze_workbook(temp_path, file.filename or "uploaded-workbook.xlsx")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot analyze workbook: {exc}",
        ) from exc
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass
