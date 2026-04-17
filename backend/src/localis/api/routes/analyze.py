"""POST /analyze — streams progress events via SSE while running the pipeline.

Final event (stage="pdf_ready") carries the full AnalysisReport payload in `detail.report`
and the reportId so the frontend can redirect to /report/[id] once it finishes.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from localis.api.deps import DiagnosticDep, StoreDep
from localis.core.errors import LocalisError, ParsingError
from localis.core.logging import get_logger
from localis.domain.schemas import AnalysisReport, ProgressEvent

logger = get_logger(__name__)
router = APIRouter(tags=["analyze"])


class AnalyzeRequest(BaseModel):
    company: str = Field(min_length=2, max_length=120)
    city: str | None = Field(default=None, max_length=80)


@router.post("/analyze/stream")
async def analyze_stream(
    payload: AnalyzeRequest,
    diagnostic: DiagnosticDep,
    store: StoreDep,
) -> EventSourceResponse:
    company = payload.company.strip()
    city = (payload.city or "").strip() or None
    if not company:
        raise HTTPException(status_code=400, detail="Company name required")

    async def event_stream() -> AsyncIterator[dict]:
        try:
            async for evt in diagnostic.run_streaming(company, city=city):
                if evt.stage == "pdf_ready" and evt.detail and "report" in evt.detail:
                    # Persist once the pipeline finishes — the HTTP consumer still gets the full report in the event.
                    report = AnalysisReport.model_validate(evt.detail["report"])
                    store.save(report)
                yield {"event": evt.stage, "data": evt.model_dump_json()}
        except ParsingError as exc:
            logger.warning("analyze.parsing_failed", error=str(exc))
            err = ProgressEvent(stage="error", message=f"Parsing failure: {exc}", progress=1.0)
            yield {"event": "error", "data": err.model_dump_json()}
        except LocalisError as exc:
            logger.warning("analyze.domain_error", error=str(exc))
            err = ProgressEvent(stage="error", message=str(exc), progress=1.0)
            yield {"event": "error", "data": err.model_dump_json()}
        except Exception as exc:  # don't leak tracebacks to clients
            logger.exception("analyze.unexpected", error=str(exc))
            err = ProgressEvent(stage="error", message="Internal error", progress=1.0)
            yield {"event": "error", "data": err.model_dump_json()}

    return EventSourceResponse(event_stream())


@router.post("/analyze", response_model=AnalysisReport)
async def analyze_sync(
    payload: AnalyzeRequest,
    diagnostic: DiagnosticDep,
    store: StoreDep,
) -> AnalysisReport:
    """Non-streaming alternative. Useful for tests and for clients that don't want SSE."""
    city = (payload.city or "").strip() or None
    try:
        report = await diagnostic.run(payload.company, city=city)
    except LocalisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    store.save(report)
    return report
