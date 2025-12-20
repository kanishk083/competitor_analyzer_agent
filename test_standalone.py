"""
Standalone Verification Script
Tests the agent pipeline without Docker.
"""

import asyncio
from rich.console import Console
from agents.pipeline import pipeline
from utils.alerting import alert_manager

console = Console()

def test_pipeline():
    console.print("\n[bold cyan]🚀 Starting Standalone Verification[/bold cyan]\n")
    
    # Test URL (using example.com as it's stable)
    test_url = "https://example.com"
    console.print(f"[bold]1. Testing Scraping & Analysis Pipeline[/bold] on {test_url}")
    
    # Run pipeline manually
    result = pipeline.scrape_and_analyze(test_url)
    
    if result.error:
        console.print(f"[red]✗ Pipeline check failed: {result.error}[/red]")
    else:
        console.print(f"[green]✓ Scraping successful[/green]")
        console.print(f"[green]✓ Content Hash: {result.analysis.impact_score if result.analysis else 'N/A'}[/green]")
        
        if result.analysis:
            console.print("\n[bold yellow]🤖 LLM Analysis Result:[/bold yellow]")
            console.print(f"Type: {result.analysis.change_type}")
            console.print(f"Summary: {result.analysis.summary}")
            console.print(f"Strategy: {result.analysis.counter_strategy}")
    
    console.print("\n[bold cyan]✅ Verification Complete[/bold cyan]")

if __name__ == "__main__":
    test_pipeline()
