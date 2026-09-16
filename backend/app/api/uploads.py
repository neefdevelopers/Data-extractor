from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.upload import FileAnalysisResponse, ImportConfirmRequest, UploadBatchOut, UploadBatchDetail, UploadRowOut
from app.schemas.common import PaginatedResponse, MessageResponse
from app.models.upload import UploadBatch, UploadRow
from app.services.excel_import_service import ExcelImportService
from app.services.sample_data_service import SampleDataService

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.post("/analyze", response_model=FileAnalysisResponse)
async def analyze_uploaded_file(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        analysis = ExcelImportService.analyze_file(contents, file.filename)
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze spreadsheet: {str(e)}")

@router.post("/confirm", response_model=UploadBatchOut)
def confirm_import(request: ImportConfirmRequest, db: Session = Depends(get_db)):
    try:
        batch = ExcelImportService.process_import(
            temp_file_id=request.temp_file_id,
            original_filename=request.file_name,
            import_type=request.import_type,
            column_mapping=request.column_mapping,
            db=db
        )
        return batch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import execution error: {str(e)}")

@router.get("", response_model=PaginatedResponse[UploadBatchOut])
def list_upload_batches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(UploadBatch).order_by(UploadBatch.uploaded_date.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{batch_id}", response_model=UploadBatchDetail)
def get_upload_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")
    
    failed_rows = db.query(UploadRow).filter(
        UploadRow.upload_id == batch_id,
        UploadRow.status == "FAILED"
    ).all()

    failed_items = [
        UploadRowOut(
            id=r.id,
            row_number=r.row_number,
            status=r.status,
            raw_data=r.raw_data,
            error_reason=r.error_reason,
            suggested_fix=r.suggested_fix
        ) for r in failed_rows
    ]

    return UploadBatchDetail(
        id=batch.id,
        file_name=batch.file_name,
        upload_type=batch.upload_type,
        uploaded_date=batch.uploaded_date,
        total_rows=batch.total_rows,
        successful_rows=batch.successful_rows,
        failed_rows=batch.failed_rows,
        duplicate_rows=batch.duplicate_rows,
        updated_rows=batch.updated_rows,
        new_customers=batch.new_customers,
        new_orders=batch.new_orders,
        new_products=batch.new_products,
        status=batch.status,
        error_message=batch.error_message,
        failed_row_items=failed_items
    )

@router.post("/generate-sample", response_model=MessageResponse)
def generate_sample_data():
    try:
        path = SampleDataService.generate_sample_excel_path()
        return MessageResponse(
            success=True,
            message="Sample Indian eCommerce dataset created in uploads folder.",
            details={"file_path": path, "file_name": "sample_indian_ecom_data.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
