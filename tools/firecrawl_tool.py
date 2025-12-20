"""
Firecrawl Scraping Tool
Alternative scraper using Firecrawl API for complex pages.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx

from config.settings import settings


@dataclass
class FirecrawlResult:
    """Result from Firecrawl API."""
    url: str
    content: str
    markdown: Optional[str] = None
    title: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class FirecrawlTool:
    """
    Web scraping tool using Firecrawl API.
    Better for JavaScript-heavy pages and complex sites.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Firecrawl API key."""
        self.api_key = api_key or settings.firecrawl_api_key
        self.base_url = "https://api.firecrawl.dev/v1"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def scrape(
        self, 
        url: str, 
        wait_for: Optional[str] = None,
        timeout: int = 30000
    ) -> FirecrawlResult:
        """
        Scrape a URL using Firecrawl API.
        
        Args:
            url: The URL to scrape
            wait_for: Optional CSS selector to wait for
            timeout: Timeout in milliseconds
            
        Returns:
            FirecrawlResult with content
        """
        if not self.api_key:
            return FirecrawlResult(
                url=url,
                content="",
                success=False,
                error="Firecrawl API key not configured"
            )
        
        try:
            payload = {
                "url": url,
                "formats": ["markdown", "html"],
                "waitFor": wait_for,
                "timeout": timeout
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/scrape",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
            data = response.json()
            
            if data.get("success"):
                return FirecrawlResult(
                    url=url,
                    content=data.get("data", {}).get("content", ""),
                    markdown=data.get("data", {}).get("markdown"),
                    title=data.get("data", {}).get("metadata", {}).get("title"),
                    success=True
                )
            else:
                return FirecrawlResult(
                    url=url,
                    content="",
                    success=False,
                    error=data.get("error", "Unknown error")
                )
                
        except httpx.TimeoutException:
            return FirecrawlResult(
                url=url,
                content="",
                success=False,
                error="Request timed out"
            )
        except Exception as e:
            return FirecrawlResult(
                url=url,
                content="",
                success=False,
                error=str(e)
            )
    
    def crawl(
        self, 
        url: str, 
        max_depth: int = 2,
        limit: int = 10
    ) -> List[FirecrawlResult]:
        """
        Crawl a website starting from URL.
        
        Args:
            url: Starting URL
            max_depth: Maximum crawl depth
            limit: Maximum number of pages
            
        Returns:
            List of FirecrawlResults
        """
        if not self.api_key:
            return [FirecrawlResult(
                url=url,
                content="",
                success=False,
                error="Firecrawl API key not configured"
            )]
        
        try:
            payload = {
                "url": url,
                "maxDepth": max_depth,
                "limit": limit,
                "scrapeOptions": {
                    "formats": ["markdown"]
                }
            }
            
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/crawl",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                
            data = response.json()
            results = []
            
            for page in data.get("data", []):
                results.append(FirecrawlResult(
                    url=page.get("metadata", {}).get("sourceURL", url),
                    content=page.get("content", ""),
                    markdown=page.get("markdown"),
                    title=page.get("metadata", {}).get("title"),
                    success=True
                ))
            
            return results
            
        except Exception as e:
            return [FirecrawlResult(
                url=url,
                content="",
                success=False,
                error=str(e)
            )]


# Create default instance
firecrawl_tool = FirecrawlTool()
