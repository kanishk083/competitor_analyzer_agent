"""
Scheduled Monitoring Script
Periodically checks competitor URLs for changes.
Alternative to changedetection.io webhooks.
"""

import json
import time
import schedule
from pathlib import Path
from rich.console import Console

from config.settings import settings
from agents.pipeline import pipeline
from utils.alerting import alert_manager


console = Console()


def load_competitors() -> list:
    """Load competitor configuration from JSON file."""
    config_path = Path(__file__).parent / "config" / "competitors.json"
    
    if not config_path.exists():
        console.print("[yellow]⚠ No competitors.json found, using empty list[/yellow]")
        return []
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return [c for c in config.get("competitors", []) if c.get("enabled", True)]


def check_competitor(competitor: dict) -> None:
    """Check a single competitor for changes."""
    name = competitor.get("name", competitor.get("url"))
    url = competitor.get("url")
    selectors = competitor.get("selectors")
    
    console.print(f"\n[cyan]🔍 Checking: {name}[/cyan]")
    
    result = pipeline.scrape_and_analyze(url, selectors)
    
    if result.error:
        console.print(f"[red]✗ Error: {result.error}[/red]")
    elif result.changed:
        console.print(f"[green]✓ Change detected and analyzed[/green]")
    else:
        console.print(f"[dim]→ No changes detected[/dim]")


def check_all_competitors() -> None:
    """Check all enabled competitors."""
    competitors = load_competitors()
    
    console.print(f"\n[bold]🔄 Running scheduled check for {len(competitors)} competitors[/bold]\n")
    
    for competitor in competitors:
        check_competitor(competitor)
    
    console.print(f"\n[bold green]✓ Scheduled check complete[/bold green]\n")


def run_scheduler(interval_minutes: int = 60) -> None:
    """
    Run the scheduler with specified interval.
    
    Args:
        interval_minutes: Check interval in minutes
    """
    console.print(f"\n[bold green]🚀 Starting Scheduled Monitor[/bold green]")
    console.print(f"   Interval: Every {interval_minutes} minutes")
    console.print(f"   Press Ctrl+C to stop\n")
    
    # Run immediately on start
    check_all_competitors()
    
    # Schedule recurring checks
    schedule.every(interval_minutes).minutes.do(check_all_competitors)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Scheduler stopped[/yellow]")


if __name__ == "__main__":
    run_scheduler(interval_minutes=2)
