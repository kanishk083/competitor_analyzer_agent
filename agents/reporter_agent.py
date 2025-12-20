"""
Reporter Agent
Generates summary reports of competitor activity.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from rich.console import Console
from rich.table import Table

from utils.storage import storage, ChangeRecord
from utils.alerting import CompetitorAlert


console = Console()


@dataclass
class CompetitorReport:
    """Summary report for a competitor."""
    url: str
    total_changes: int
    changes_by_type: Dict[str, int] = field(default_factory=dict)
    avg_impact: float = 0.0
    recent_changes: List[ChangeRecord] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class ReporterAgent:
    """
    Agent for generating competitor activity reports.
    Summarizes changes and provides strategic insights.
    """
    
    def generate_report(
        self, 
        url: str, 
        days: int = 30
    ) -> CompetitorReport:
        """
        Generate a report for a specific competitor URL.
        
        Args:
            url: Competitor URL to report on
            days: Number of days to include
            
        Returns:
            CompetitorReport with summary data
        """
        history = storage.get_change_history(url, limit=100)
        
        # Filter to requested time period
        cutoff = datetime.now() - timedelta(days=days)
        recent = [h for h in history if h.detected_at and h.detected_at > cutoff]
        
        # Calculate statistics
        changes_by_type: Dict[str, int] = {}
        total_impact = 0
        impact_count = 0
        
        for change in recent:
            if change.analysis_result:
                try:
                    import json
                    analysis = json.loads(change.analysis_result)
                    change_type = analysis.get("change_type", "Unknown")
                    impact = analysis.get("impact_score", 0)
                    
                    changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1
                    total_impact += impact
                    impact_count += 1
                except:
                    pass
        
        avg_impact = total_impact / impact_count if impact_count > 0 else 0
        
        return CompetitorReport(
            url=url,
            total_changes=len(recent),
            changes_by_type=changes_by_type,
            avg_impact=round(avg_impact, 1),
            recent_changes=recent[:10],
            recommendations=self._generate_recommendations(changes_by_type, avg_impact)
        )
    
    def _generate_recommendations(
        self, 
        changes_by_type: Dict[str, int],
        avg_impact: float
    ) -> List[str]:
        """Generate strategic recommendations based on activity."""
        recommendations = []
        
        pricing_changes = changes_by_type.get("Pricing", 0)
        feature_changes = changes_by_type.get("Feature", 0)
        marketing_changes = changes_by_type.get("Marketing", 0)
        
        if pricing_changes > 2:
            recommendations.append(
                "⚠️ High pricing activity detected - review competitive positioning"
            )
        
        if feature_changes > 3:
            recommendations.append(
                "🚀 Competitor is actively developing features - accelerate roadmap"
            )
        
        if marketing_changes > 3:
            recommendations.append(
                "📢 Marketing push detected - increase brand visibility"
            )
        
        if avg_impact >= 7:
            recommendations.append(
                "🔴 High-impact changes detected - schedule competitive review"
            )
        
        if not recommendations:
            recommendations.append("✅ No significant competitive threats detected")
        
        return recommendations
    
    def print_report(self, report: CompetitorReport) -> None:
        """Print a formatted report to console."""
        console.print(f"\n[bold]📊 Competitor Report: {report.url}[/bold]\n")
        
        # Summary table
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value")
        
        table.add_row("Total Changes", str(report.total_changes))
        table.add_row("Avg Impact", f"{report.avg_impact}/10")
        
        for change_type, count in report.changes_by_type.items():
            table.add_row(f"  {change_type}", str(count))
        
        console.print(table)
        
        # Recommendations
        console.print("\n[bold]💡 Recommendations:[/bold]")
        for rec in report.recommendations:
            console.print(f"  {rec}")
        
        console.print()
    
    def generate_all_reports(self, days: int = 30) -> List[CompetitorReport]:
        """Generate reports for all monitored URLs."""
        urls = storage.get_all_monitored_urls()
        reports = []
        
        for url_info in urls:
            report = self.generate_report(url_info["url"], days)
            reports.append(report)
        
        return reports


# Global reporter instance
reporter_agent = ReporterAgent()
