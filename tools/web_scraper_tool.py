"""
Web Scraper Tool
Standalone scraping tool with CSS selector targeting and hash generation.
"""

import hashlib
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from bs4 import BeautifulSoup


@dataclass
class ScrapeResult:
    """Result of a scraping operation."""
    url: str
    content: str
    content_hash: str
    selectors_matched: List[str] = field(default_factory=list)
    title: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class WebScraperTool:
    """
    Standalone web scraping tool with:
    - CSS selector targeting
    - SHA-256 hash generation
    - BeautifulSoup integration
    """
    
    def __init__(self, user_agent: Optional[str] = None, timeout: int = 30):
        """Initialize scraper with configuration."""
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content."""
        normalized = " ".join(content.split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def scrape(
        self, 
        url: str, 
        selectors: Optional[List[str]] = None
    ) -> ScrapeResult:
        """
        Scrape a URL and extract content based on CSS selectors.
        
        Args:
            url: The URL to scrape
            selectors: Optional list of CSS selectors to target
            
        Returns:
            ScrapeResult with content and hash
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get page title
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else None
            
            content_parts = []
            matched_selectors = []
            
            if selectors:
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        matched_selectors.append(selector)
                        for elem in elements:
                            text = elem.get_text(separator=' ', strip=True)
                            if text:
                                content_parts.append(text)
            
            # Fallback to body if no selectors matched
            if not content_parts:
                body = soup.find('body')
                if body:
                    content_parts.append(body.get_text(separator=' ', strip=True))
                    matched_selectors.append('body (fallback)')
            
            content = '\n\n'.join(content_parts)
            content_hash = self.compute_hash(content)
            
            return ScrapeResult(
                url=url,
                content=content,
                content_hash=content_hash,
                selectors_matched=matched_selectors,
                title=title,
                success=True
            )
            
        except requests.Timeout:
            return ScrapeResult(
                url=url,
                content="",
                content_hash="",
                success=False,
                error=f"Request timed out after {self.timeout} seconds"
            )
        except requests.RequestException as e:
            return ScrapeResult(
                url=url,
                content="",
                content_hash="",
                success=False,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return ScrapeResult(
                url=url,
                content="",
                content_hash="",
                success=False,
                error=f"Scraping failed: {str(e)}"
            )
    
    def scrape_pricing(self, url: str) -> ScrapeResult:
        """Scrape pricing-specific content."""
        pricing_selectors = [
            "#pricing-table", "#pricing", ".pricing",
            ".pricing-section", ".price", ".pricing-card",
            ".plan", ".plans", ".tier", ".subscription",
            "[data-pricing]", "[data-plan]"
        ]
        return self.scrape(url, pricing_selectors)
    
    def scrape_features(self, url: str) -> ScrapeResult:
        """Scrape feature-specific content."""
        feature_selectors = [
            "#features", ".features", ".feature-list",
            ".product-features", ".feature-section",
            ".capabilities", ".benefits",
            "[data-features]"
        ]
        return self.scrape(url, feature_selectors)
    
    def scrape_multiple(
        self, 
        configs: List[Dict[str, Any]]
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs with their configurations.
        
        Args:
            configs: List of dicts with 'url' and optional 'selectors'
            
        Returns:
            List of ScrapeResults
        """
        results = []
        for config in configs:
            url = config.get('url')
            selectors = config.get('selectors')
            if url:
                result = self.scrape(url, selectors)
                results.append(result)
        return results


# Create default instance
web_scraper_tool = WebScraperTool()
