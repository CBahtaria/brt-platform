import logging

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest")
async def ingest_document(request: Request, file: UploadFile = File(...)):
    tenant_id = request.state.tenant_id
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")
    contents = await file.read()
    logger.info(f"Ingest: tenant={tenant_id} file={file.filename} size={len(contents)}B")
    # Phase 0 placeholder: real ingest pipeline (chunk → embed → upsert) goes here
    return {
        "status": "received",
        "tenant_id": tenant_id,
        "filename": file.filename,
        "size_bytes": len(contents),
        "message": "Document received. Full ingest pipeline coming in Phase 1.",
    }
