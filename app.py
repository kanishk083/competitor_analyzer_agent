"""
Competitor Analyzer Agent - FastAPI Application
Webhook listener for changedetection.io with differential analysis.
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rich.console import Console

from config.settings import settings
from utils.storage import storage
from utils.alerting import alert_manager
from agents.pipeline import pipeline, PipelineResult


console = Console()


# ===========================================
# Pydantic Models
# ===========================================

class WebhookPayload(BaseModel):
    """Payload received from changedetection.io webhook."""
    url: str = Field(..., description="The URL that was monitored")
    current_snapshot: Optional[str] = Field(None, description="The new/current text content")
    watch_url: Optional[str] = Field(None, description="Alternative URL field")
    watch_uuid: Optional[str] = Field(None, description="Unique watch identifier")
    
    # Additional fields that might be present
    check_count: Optional[int] = None
    last_changed: Optional[str] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class ManualCheckRequest(BaseModel):
    """Request to manually check a URL."""
    url: str = Field(..., description="URL to check")
    selectors: Optional[List[str]] = Field(None, description="CSS selectors to target")


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""
    url: str
    changed: bool
    analyzed: bool
    alert_sent: bool
    change_type: Optional[str] = None
    impact_score: Optional[int] = None
    summary: Optional[str] = None
    counter_strategy: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0


# ===========================================
# Application Lifecycle
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    console.print("\n[bold green]🚀 Competitor Analyzer Agent Starting...[/bold green]\n")
    alert_manager.send_startup_notification()
    yield
    # Shutdown
    console.print("\n[bold yellow]👋 Shutting down...[/bold yellow]\n")


# ===========================================
# FastAPI Application
# ===========================================

app = FastAPI(
    title="Competitor Analyzer Agent",
    description="Webhook listener for competitor website monitoring with LLM-powered analysis",
    version="1.0.0",
    lifespan=lifespan
)


# ===========================================
# Webhook Endpoints
# ===========================================

@app.post("/webhook/change", response_model=AnalysisResponse)
async def receive_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Receive webhook from changedetection.io when a monitored page changes.
    
    This endpoint:
    1. Extracts URL and content from payload
    2. Performs differential analysis (hash comparison)
    3. If changed: Analyzes with LLM
    4. If high impact: Sends alerts
    """
    # Extract URL (try multiple fields)
    url = payload.url or payload.watch_url
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided in webhook payload")
    
    # Extract content
    content = payload.current_snapshot
    if not content:
        raise HTTPException(status_code=400, detail="No content snapshot in webhook payload")
    
    console.print(f"\n[bold cyan]📥 Webhook received for: {url}[/bold cyan]")
    
    # Process through pipeline
    result = pipeline.process_webhook(url, content)
    
    return _pipeline_result_to_response(result)


@app.post("/webhook/raw")
async def receive_raw_webhook(request: Request) -> Dict[str, Any]:
    """
    Receive raw webhook for debugging.
    Logs the full payload without processing.
    """
    try:
        body = await request.json()
        console.print("\n[bold yellow]📥 Raw webhook received:[/bold yellow]")
        console.print_json(json.dumps(body, default=str))
        return {"status": "received", "payload": body}
    except Exception as e:
        console.print(f"[red]Error parsing webhook: {e}[/red]")
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================
# Manual Check Endpoints
# ===========================================

@app.post("/check", response_model=AnalysisResponse)
async def manual_check(request: ManualCheckRequest) -> AnalysisResponse:
    """
    Manually trigger a check for a specific URL.
    Useful for on-demand competitor analysis.
    """
    console.print(f"\n[bold cyan]🔍 Manual check requested for: {request.url}[/bold cyan]")
    
    result = pipeline.scrape_and_analyze(
        url=request.url,
        selectors=request.selectors
    )
    
    return _pipeline_result_to_response(result)


# ===========================================
# History & Status Endpoints
# ===========================================

@app.get("/history/{url:path}")
async def get_url_history(url: str, limit: int = 10) -> Dict[str, Any]:
    """Get change history for a specific URL."""
    history = storage.get_change_history(url, limit=limit)
    return {
        "url": url,
        "changes": [
            {
                "id": r.id,
                "hash": r.content_hash,
                "preview": r.content_preview[:200] if r.content_preview else None,
                "detected_at": r.detected_at.isoformat() if r.detected_at else None,
                "analysis": r.analysis_result
            }
            for r in history
        ]
    }


@app.get("/monitored")
async def list_monitored_urls() -> Dict[str, Any]:
    """List all monitored URLs with their last update times."""
    urls = storage.get_all_monitored_urls()
    return {"count": len(urls), "urls": urls}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": settings.groq_model
    }


# ===========================================
# Helper Functions
# ===========================================

def _pipeline_result_to_response(result: PipelineResult) -> AnalysisResponse:
    """Convert PipelineResult to API response."""
    response = AnalysisResponse(
        url=result.url,
        changed=result.changed,
        analyzed=result.analyzed,
        alert_sent=result.alert_sent,
        error=result.error,
        execution_time_ms=result.execution_time_ms
    )
    
    if result.analysis:
        response.change_type = result.analysis.change_type
        response.impact_score = result.analysis.impact_score
        response.summary = result.analysis.summary
        response.counter_strategy = result.analysis.counter_strategy
    
    return response


# ===========================================
# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
# ===========================================
