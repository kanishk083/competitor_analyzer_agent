"""
SWOT Agent
Generates SWOT analysis based on competitor monitoring data.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from groq import Groq
import json

from config.settings import settings
from utils.storage import storage


@dataclass
class SWOTAnalysis:
    """SWOT analysis result."""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    competitor_url: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


class SWOTAgent:
    """
    Agent for generating SWOT analysis from competitor data.
    Uses LLM to synthesize competitive intelligence.
    """
    
    def __init__(self):
        """Initialize with GROQ client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    def generate_swot(
        self, 
        competitor_url: str,
        our_company_context: str = ""
    ) -> SWOTAnalysis:
        """
        Generate SWOT analysis based on competitor monitoring data.
        
        Args:
            competitor_url: The competitor URL to analyze
            our_company_context: Optional context about our company
            
        Returns:
            SWOTAnalysis with strategic insights
        """
        # Get historical data for this competitor
        history = storage.get_change_history(competitor_url, limit=20)
        
        if not history:
            return SWOTAnalysis(
                competitor_url=competitor_url,
                success=False,
                error="No monitoring data available for this competitor"
            )
        
        # Compile change summaries
        changes_summary = []
        for record in history:
            if record.analysis_result:
                try:
                    analysis = json.loads(record.analysis_result)
                    changes_summary.append({
                        "type": analysis.get("change_type"),
                        "impact": analysis.get("impact_score"),
                        "summary": analysis.get("summary")
                    })
                except:
                    pass
        
        if not changes_summary:
            return SWOTAnalysis(
                competitor_url=competitor_url,
                success=False,
                error="No analyzed changes available"
            )
        
        # Generate SWOT with LLM
        return self._generate_with_llm(competitor_url, changes_summary, our_company_context)
    
    def _generate_with_llm(
        self,
        competitor_url: str,
        changes: List[Dict],
        our_context: str
    ) -> SWOTAnalysis:
        """Generate SWOT analysis using LLM."""
        prompt = f"""You are a strategic analyst. Based on the following competitor activity data, generate a SWOT analysis for our company's competitive positioning.

## Competitor: {competitor_url}

## Recent Competitor Changes:
{json.dumps(changes, indent=2)}

## Our Company Context:
{our_context or "General B2B SaaS company"}

## Instructions:
Generate a SWOT analysis that helps us respond to this competitor's activity.

## Response Format (JSON):
{{
    "strengths": ["Our strength 1", "Our strength 2"],
    "weaknesses": ["Our weakness 1", "Our weakness 2"],
    "opportunities": ["Opportunity 1", "Opportunity 2"],
    "threats": ["Threat from competitor 1", "Threat 2"]
}}

Provide 2-4 items per category. Be specific and actionable.
Respond ONLY with valid JSON."""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a strategic business analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            
            return SWOTAnalysis(
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                opportunities=data.get("opportunities", []),
                threats=data.get("threats", []),
                competitor_url=competitor_url,
                success=True
            )
            
        except Exception as e:
            return SWOTAnalysis(
                competitor_url=competitor_url,
                success=False,
                error=str(e)
            )
    
    def print_swot(self, swot: SWOTAnalysis) -> None:
        """Print formatted SWOT analysis."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.columns import Columns
        
        console = Console()
        
        if not swot.success:
            console.print(f"[red]SWOT generation failed: {swot.error}[/red]")
            return
        
        console.print(f"\n[bold]📊 SWOT Analysis: {swot.competitor_url}[/bold]\n")
        
        # Create panels for each quadrant
        s_content = "\n".join(f"• {s}" for s in swot.strengths)
        w_content = "\n".join(f"• {w}" for w in swot.weaknesses)
        o_content = "\n".join(f"• {o}" for o in swot.opportunities)
        t_content = "\n".join(f"• {t}" for t in swot.threats)
        
        console.print(Panel(s_content, title="💪 Strengths", border_style="green"))
        console.print(Panel(w_content, title="⚠️ Weaknesses", border_style="yellow"))
        console.print(Panel(o_content, title="🚀 Opportunities", border_style="blue"))
        console.print(Panel(t_content, title="🔴 Threats", border_style="red"))


# Global SWOT agent instance
swot_agent = SWOTAgent()
