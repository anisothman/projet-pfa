"""GET /reports/{id} and GET /reports/{id}/pdf — serve cached reports."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from localis.api.deps import PDFDep, StoreDep
from localis.domain.schemas import AnalysisReport

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}", response_model=AnalysisReport)
async def get_report(report_id: str, store: StoreDep) -> AnalysisReport:
    report = store.load(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/pdf")
async def get_report_pdf(report_id: str, store: StoreDep, pdf: PDFDep) -> Response:
    report = store.load(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    path = store.pdf_path(report_id)
    if path.exists():
        return Response(
            content=path.read_bytes(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{report.entreprise.nom}.pdf"'},
        )

    # Lazy build + cache to disk.
    data = pdf.build(report)
    path.write_bytes(data)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report.entreprise.nom}.pdf"'},
    )
