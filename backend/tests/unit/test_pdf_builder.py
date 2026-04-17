"""Smoke test: PDF builder produces valid bytes from a canned AnalysisReport."""

from localis.services.pdf.builder import PDFReportBuilder


def test_pdf_builder_produces_valid_pdf(sample_report):
    data = PDFReportBuilder().build(sample_report)

    assert isinstance(data, bytes)
    assert data.startswith(b"%PDF-")
    assert data.endswith(b"%%EOF\n") or data.rstrip().endswith(b"%%EOF")
    assert len(data) > 2000  # A minimal non-empty report
