from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from localis.domain.schemas import AnalysisReport
from localis.services.pdf.canvas import ReportCanvas
from localis.services.pdf.sections import (
    build_action_plan,
    build_cover,
    build_footer_metadata,
    build_swot,
)
from localis.services.pdf.styles import Palette, make_styles

W, H = A4


def _paint_background(canvas, _doc) -> None:
    canvas.saveState()
    canvas.setFillColor(Palette.BG)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.restoreState()


class PDFReportBuilder:
    def __init__(self) -> None:
        self._styles = make_styles()

    def build(self, report: AnalysisReport) -> bytes:
        buffer = BytesIO()
        date_str = report.metadonnees.date_analyse.strftime("%d/%m/%Y %H:%M")
        provider_label = self._provider_label(report)

        def canvas_factory(*args, **kwargs):
            return ReportCanvas(
                *args,
                company=report.entreprise.nom,
                date_str=date_str,
                provider=provider_label,
                **kwargs,
            )

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.8 * cm,
            rightMargin=1.8 * cm,
            topMargin=3 * cm,
            bottomMargin=1.8 * cm,
            title=f"Localis AI — {report.entreprise.nom}",
            author="Localis AI",
        )
        story = [
            *build_cover(report, self._styles),
            *build_swot(report.diagnostic, self._styles),
            *build_action_plan(report.plan_action, self._styles),
            *build_footer_metadata(report, self._styles),
        ]
        doc.build(
            story,
            canvasmaker=canvas_factory,
            onFirstPage=_paint_background,
            onLaterPages=_paint_background,
        )
        return buffer.getvalue()

    @staticmethod
    def _provider_label(report: AnalysisReport) -> str:
        meta = report.metadonnees
        if meta.provider and meta.modele:
            return f"{meta.provider} · {meta.modele}"
        return meta.provider or meta.modele or ""
