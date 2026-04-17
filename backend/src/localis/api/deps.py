"""FastAPI dependency providers. Singletons cached via lru_cache where safe."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from localis.core.config import Settings, get_settings
from localis.services.diagnostic import DiagnosticService, ReportStore
from localis.services.llm.router import LLMRouter, build_router
from localis.services.pdf.builder import PDFReportBuilder
from localis.services.serp import SerpClient

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache(maxsize=1)
def _llm_singleton() -> LLMRouter:
    return build_router(get_settings())


@lru_cache(maxsize=1)
def _serp_singleton() -> SerpClient:
    s = get_settings()
    assert s.serp_api_key, "SERP_API_KEY is required (checked at startup)"
    return SerpClient(api_key=s.serp_api_key)


@lru_cache(maxsize=1)
def _store_singleton() -> ReportStore:
    return ReportStore(reports_dir=get_settings().reports_dir)


@lru_cache(maxsize=1)
def _pdf_singleton() -> PDFReportBuilder:
    return PDFReportBuilder()


def get_diagnostic_service() -> DiagnosticService:
    return DiagnosticService(serp=_serp_singleton(), llm=_llm_singleton())


def get_store() -> ReportStore:
    return _store_singleton()


def get_pdf_builder() -> PDFReportBuilder:
    return _pdf_singleton()


DiagnosticDep = Annotated[DiagnosticService, Depends(get_diagnostic_service)]
StoreDep = Annotated[ReportStore, Depends(get_store)]
PDFDep = Annotated[PDFReportBuilder, Depends(get_pdf_builder)]
