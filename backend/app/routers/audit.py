from fastapi import APIRouter, Response

from app.audit import service as audit_service

router = APIRouter()


@router.get("/audit/export")
def export_audit_csv() -> Response:
    csv_data = audit_service.export_csv()
    return Response(content=csv_data, media_type="text/csv")
