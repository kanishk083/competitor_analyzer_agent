"""
Multi-Agent Pipeline Orchestration
Coordinates Monitor → Scrape → Analyze → Alert workflow.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from rich.console import Console

from utils.storage import HashStorage, storage
from utils.alerting import AlertManager, alert_manager, CompetitorAlert
from agents.scraper_agent import ScraperAgent, scraper_agent, ScrapedContent
from agents.analyzer_agent import AnalyzerAgent, analyzer_agent, AnalysisResult


console = Console()


@dataclass
class PipelineResult:
    """Result of a pipeline execution."""
    url: str
    changed: bool
    analyzed: bool
    alert_sent: bool
    analysis: Optional[AnalysisResult] = None
    error: Optional[str] = None
    execution_time_ms: float = 0


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""
    impact_threshold: int = 5  # Minimum impact score to send alert
    skip_analysis_on_no_change: bool = True
    save_to_history: bool = True


class CompetitorPipeline:
    """
    Orchestrates the competitor analysis pipeline.
    
    Flow:
    1. Receive content (from webhook or manual scrape)
    2. Differential analysis (hash comparison)
    3. If changed: LLM analysis
    4. If high impact: Send alerts
    """
    
    def __init__(
        self,
        storage: HashStorage = storage,
        scraper: ScraperAgent = scraper_agent,
        analyzer: AnalyzerAgent = analyzer_agent,
        alerter: AlertManager = alert_manager,
        config: Optional[PipelineConfig] = None
    ):
        """Initialize pipeline with dependencies."""
        self.storage = storage
        self.scraper = scraper
        self.analyzer = analyzer
        self.alerter = alerter
        self.config = config or PipelineConfig()
    
    def process_webhook(
        self, 
        url: str, 
        current_snapshot: str
    ) -> PipelineResult:
        """
        Process a webhook from changedetection.io.
        
        Args:
            url: The URL that changed
            current_snapshot: The new content text
            
        Returns:
            PipelineResult with execution details
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Differential Analysis - Compare hashes
            new_hash = self.storage.compute_hash(current_snapshot)
            old_hash = self.storage.get_last_hash(url)
            previous_content = self.storage.get_last_content(url)
            
            has_changed = new_hash != old_hash
            
            if not has_changed and self.config.skip_analysis_on_no_change:
                # No change detected - skip LLM call to save costs
                console.print(f"[dim]→ No actual change detected for: {url}[/dim]")
                return PipelineResult(
                    url=url,
                    changed=False,
                    analyzed=False,
                    alert_sent=False,
                    execution_time_ms=self._elapsed_ms(start_time)
                )
            
            # Step 2: Analyze with LLM
            console.print(f"[cyan]→ Change detected, analyzing: {url}[/cyan]")
            analysis = self.analyzer.analyze_change(
                url=url,
                content=current_snapshot,
                previous_content=previous_content
            )
            
            # Step 3: Update storage with new hash
            if self.config.save_to_history:
                self.storage.update_hash(
                    url=url,
                    content_hash=new_hash,
                    content=current_snapshot,
                    analysis_result=analysis.raw_response
                )
            
            # Step 4: Send alert if impact is high enough
            alert_sent = False
            if analysis.success and analysis.impact_score >= self.config.impact_threshold:
                alert = self.analyzer.create_alert(url, analysis)
                self.alerter.send_alert(alert)
                alert_sent = True
            else:
                console.print(
                    f"[dim]→ Impact score ({analysis.impact_score}) below threshold "
                    f"({self.config.impact_threshold}), no alert sent[/dim]"
                )
            
            return PipelineResult(
                url=url,
                changed=True,
                analyzed=True,
                alert_sent=alert_sent,
                analysis=analysis,
                execution_time_ms=self._elapsed_ms(start_time)
            )
            
        except Exception as e:
            console.print(f"[red]✗ Pipeline error: {e}[/red]")
            return PipelineResult(
                url=url,
                changed=False,
                analyzed=False,
                alert_sent=False,
                error=str(e),
                execution_time_ms=self._elapsed_ms(start_time)
            )
    
    def scrape_and_analyze(
        self, 
        url: str, 
        selectors: Optional[list] = None
    ) -> PipelineResult:
        """
        Manually scrape a URL and run analysis.
        Useful for on-demand competitor checking.
        
        Args:
            url: The URL to scrape
            selectors: Optional CSS selectors to target
            
        Returns:
            PipelineResult with execution details
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Scrape the URL
            console.print(f"[cyan]→ Scraping: {url}[/cyan]")
            scraped = self.scraper.scrape_url(url, selectors)
            
            if not scraped.success:
                return PipelineResult(
                    url=url,
                    changed=False,
                    analyzed=False,
                    alert_sent=False,
                    error=scraped.error_message,
                    execution_time_ms=self._elapsed_ms(start_time)
                )
            
            # Step 2: Process through webhook handler (reuse logic)
            return self.process_webhook(url, scraped.content)
            
        except Exception as e:
            return PipelineResult(
                url=url,
                changed=False,
                analyzed=False,
                alert_sent=False,
                error=str(e),
                execution_time_ms=self._elapsed_ms(start_time)
            )
    
    def _elapsed_ms(self, start_time: datetime) -> float:
        """Calculate elapsed time in milliseconds."""
        return (datetime.now() - start_time).total_seconds() * 1000


# Global pipeline instance
pipeline = CompetitorPipeline()
