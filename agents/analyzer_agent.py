"""
Analyzer Agent
Uses GROQ LLM (Llama 3.3) to analyze competitor website changes.
Classifies changes and generates counter-strategies.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from groq import Groq

from config.settings import settings
from utils.alerting import CompetitorAlert


@dataclass
class AnalysisResult:
    """Represents the LLM analysis of a competitor change."""
    change_type: str  # 'Pricing', 'Feature', 'Marketing'
    impact_score: int  # 1-10
    summary: str
    counter_strategy: str
    raw_response: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class AnalyzerAgent:
    """
    Agent for analyzing competitor website changes using GROQ LLM.
    Classifies changes and generates actionable counter-strategies.
    """
    
    def __init__(self):
        """Initialize analyzer with GROQ client."""
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    def _build_analysis_prompt(self, url: str, content: str, previous_content: Optional[str] = None) -> str:
        """Build the analysis prompt for the LLM."""
        
        diff_section = ""
        if previous_content:
            diff_section = f"""
## Previous Content (for comparison):
{previous_content[:2000]}

"""
        
        prompt = f"""You are a competitive intelligence analyst. Analyze the following competitor website change and provide strategic insights.

## URL Being Monitored:
{url}

## Current Content (New/Changed):
{content[:4000]}
{diff_section}
## Instructions:
1. **Classify the change**: Determine if this is primarily a 'Pricing', 'Feature', or 'Marketing' change.
2. **Determine business impact**: Rate the competitive impact from 1-10:
   - 1-3: Minor change, low competitive threat
   - 4-6: Moderate change, worth monitoring
   - 7-10: Significant change, requires immediate attention
3. **Summarize the change**: What specifically changed and why does it matter?
4. **Counter-strategy**: Draft a 1-sentence actionable recommendation for our Sales team.

## Response Format (JSON):
{{
    "change_type": "Pricing|Feature|Marketing",
    "impact_score": 1-10,
    "summary": "Brief summary of what changed",
    "counter_strategy": "One actionable sentence for Sales team"
}}

Respond ONLY with valid JSON, no additional text."""

        return prompt
    
    def analyze_change(
        self, 
        url: str, 
        content: str, 
        previous_content: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze a competitor website change using the LLM.
        
        Args:
            url: The URL that changed
            content: The new/current content
            previous_content: Optional previous content for comparison
            
        Returns:
            AnalysisResult with classification and recommendations
        """
        try:
            prompt = self._build_analysis_prompt(url, content, previous_content)
            
            # Call GROQ API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a competitive intelligence analyst. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            response_text = chat_completion.choices[0].message.content
            analysis_data = json.loads(response_text)
            
            return AnalysisResult(
                change_type=analysis_data.get("change_type", "Unknown"),
                impact_score=min(10, max(1, int(analysis_data.get("impact_score", 5)))),
                summary=analysis_data.get("summary", "No summary available"),
                counter_strategy=analysis_data.get("counter_strategy", "No strategy available"),
                raw_response=response_text,
                success=True
            )
            
        except json.JSONDecodeError as e:
            return AnalysisResult(
                change_type="Unknown",
                impact_score=5,
                summary="Failed to parse LLM response",
                counter_strategy="Manual review required",
                error_message=f"JSON parse error: {str(e)}",
                success=False
            )
        except Exception as e:
            return AnalysisResult(
                change_type="Unknown",
                impact_score=5,
                summary="Analysis failed",
                counter_strategy="Manual review required",
                error_message=f"Analysis error: {str(e)}",
                success=False
            )
    
    def create_alert(
        self, 
        url: str, 
        analysis: AnalysisResult
    ) -> CompetitorAlert:
        """
        Create a CompetitorAlert from analysis results.
        
        Args:
            url: The URL that was analyzed
            analysis: The analysis result from LLM
            
        Returns:
            CompetitorAlert ready for delivery
        """
        return CompetitorAlert(
            url=url,
            change_type=analysis.change_type,
            impact_score=analysis.impact_score,
            summary=analysis.summary,
            counter_strategy=analysis.counter_strategy,
            detected_at=datetime.now()
        )
    
    def should_alert(self, analysis: AnalysisResult, threshold: int = 5) -> bool:
        """
        Determine if an analysis result warrants an alert.
        
        Args:
            analysis: The analysis result
            threshold: Minimum impact score to trigger alert (default 5)
            
        Returns:
            True if alert should be sent
        """
        return analysis.success and analysis.impact_score >= threshold


# Global analyzer instance
analyzer_agent = AnalyzerAgent()
