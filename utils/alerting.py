"""
Alert Delivery System
Sends formatted alerts to console and Slack when competitor changes are detected.
"""

import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from dataclasses import dataclass

from config.settings import settings


# Rich console for formatted output
console = Console()


@dataclass
class CompetitorAlert:
    """Represents a competitor change alert."""
    url: str
    change_type: str  # 'Pricing', 'Feature', 'Marketing'
    impact_score: int  # 1-10
    summary: str
    counter_strategy: str
    raw_content: Optional[str] = None
    detected_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "url": self.url,
            "change_type": self.change_type,
            "impact_score": self.impact_score,
            "summary": self.summary,
            "counter_strategy": self.counter_strategy,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None
        }


class AlertManager:
    """Manages alert delivery to various channels."""
    
    def __init__(self):
        self.slack_webhook_url = settings.slack_webhook_url
        self.console = Console()
    
    def send_alert(self, alert: CompetitorAlert) -> None:
        """Send alert to all configured channels."""
        # Always send to console
        self._send_console_alert(alert)
        
        # Send to Slack if configured
        if self.slack_webhook_url:
            self._send_slack_alert(alert)
    
    def _get_impact_color(self, score: int) -> str:
        """Get color based on impact score."""
        if score >= 8:
            return "red"
        elif score >= 5:
            return "yellow"
        else:
            return "green"
    
    def _get_type_emoji(self, change_type: str) -> str:
        """Get emoji for change type."""
        emojis = {
            "Pricing": "💰",
            "Feature": "🚀",
            "Marketing": "📢"
        }
        return emojis.get(change_type, "📋")
    
    def _send_console_alert(self, alert: CompetitorAlert) -> None:
        """Send formatted alert to console using Rich."""
        impact_color = self._get_impact_color(alert.impact_score)
        emoji = self._get_type_emoji(alert.change_type)
        
        # Create alert panel
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="bold cyan")
        table.add_column("Value")
        
        table.add_row("🔗 URL", alert.url)
        table.add_row(f"{emoji} Type", alert.change_type)
        table.add_row("📊 Impact", Text(f"{alert.impact_score}/10", style=f"bold {impact_color}"))
        table.add_row("📝 Summary", alert.summary)
        table.add_row("⚔️ Counter-Strategy", Text(alert.counter_strategy, style="bold green"))
        
        if alert.detected_at:
            table.add_row("🕐 Detected", alert.detected_at.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Determine border color based on impact
        border_style = impact_color
        title = f"🚨 COMPETITOR ALERT: {alert.change_type.upper()} CHANGE"
        
        panel = Panel(
            table,
            title=title,
            border_style=border_style,
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def _send_slack_alert(self, alert: CompetitorAlert) -> None:
        """Send alert to Slack webhook."""
        if not self.slack_webhook_url:
            return
        
        emoji = self._get_type_emoji(alert.change_type)
        impact_emoji = "🔴" if alert.impact_score >= 8 else ("🟡" if alert.impact_score >= 5 else "🟢")
        
        # Format Slack message with blocks
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 Competitor Alert: {alert.change_type} Change",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*URL:*\n<{alert.url}|View Page>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:*\n{emoji} {alert.change_type}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Impact:*\n{impact_emoji} {alert.impact_score}/10"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Detected:*\n{alert.detected_at.strftime('%Y-%m-%d %H:%M') if alert.detected_at else 'Now'}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Summary:*\n{alert.summary}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*💡 Counter-Strategy:*\n_{alert.counter_strategy}_"
                    }
                },
                {
                    "type": "divider"
                }
            ]
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.slack_webhook_url,
                    json=message,
                    timeout=10.0
                )
                response.raise_for_status()
                console.print("[green]✓ Slack alert sent successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to send Slack alert: {e}[/red]")
    
    def send_startup_notification(self) -> None:
        """Send notification that the monitoring system has started."""
        panel = Panel(
            "[bold green]Competitor Analyzer Agent Started[/bold green]\n\n"
            "• Webhook listener active\n"
            "• Differential analysis enabled\n"
            "• GROQ LLM integration ready",
            title="🤖 System Status",
            border_style="green"
        )
        self.console.print(panel)
    
    def send_no_change_notification(self, url: str) -> None:
        """Log when no change was detected (optional, for debugging)."""
        console.print(f"[dim]No changes detected for: {url}[/dim]")


# Global alert manager instance
alert_manager = AlertManager()
