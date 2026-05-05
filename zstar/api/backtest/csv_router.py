import shutil
from typing import Annotated
from fastapi import APIRouter, File, HTTPException, UploadFile

from zstar.api.utils import ensure_data_dir, list_csv_filenames, normalize_csv_filename
from zstar.core.exceptions import BacktestServiceError

from .models import CsvFileUploadResponse, CsvFilesListResponse


router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.get("/csv-files")
def get_csv_files() -> CsvFilesListResponse:
    return CsvFilesListResponse(files=list_csv_filenames())


@router.post("/csv-files")
def upload_csv_file(file: Annotated[UploadFile, File(...)]) -> CsvFileUploadResponse:
    try:
        filename = normalize_csv_filename(file.filename or "")
        destination = ensure_data_dir() / filename
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)
    except BacktestServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=f"{exc.error_code}:\n- {str(exc)}") from exc

    return CsvFileUploadResponse(filename=filename, files=list_csv_filenames())
