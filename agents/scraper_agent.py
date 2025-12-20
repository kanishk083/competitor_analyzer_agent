"""
Scraper Agent
Uses BeautifulSoup and CSS selectors for targeted web scraping.
"""

import requests
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from dataclasses import dataclass

from config.settings import settings


@dataclass
class ScrapedContent:
    """Represents scraped content from a URL."""
    url: str
    content: str
    selector_used: Optional[str] = None
    title: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class ScraperAgent:
    """
    Agent for scraping targeted content from competitor websites.
    Uses BeautifulSoup with CSS selectors to extract specific data.
    """
    
    def __init__(self, user_agent: Optional[str] = None):
        """Initialize scraper with optional custom user agent."""
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
    
    def scrape_url(
        self, 
        url: str, 
        selectors: Optional[List[str]] = None,
        timeout: int = 30
    ) -> ScrapedContent:
        """
        Scrape content from a URL using optional CSS selectors.
        
        Args:
            url: The URL to scrape
            selectors: List of CSS selectors to target specific elements
            timeout: Request timeout in seconds
            
        Returns:
            ScrapedContent with extracted text
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get page title
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else None
            
            # If selectors provided, extract only those elements
            if selectors:
                content_parts = []
                used_selector = None
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        used_selector = selector
                        for element in elements:
                            # Get text and clean it
                            text = element.get_text(separator=' ', strip=True)
                            if text:
                                content_parts.append(text)
                
                content = '\n\n'.join(content_parts)
                
                if not content:
                    # Fallback to body if no selectors matched
                    body = soup.find('body')
                    content = body.get_text(separator=' ', strip=True) if body else ""
                    used_selector = "body (fallback)"
                
                return ScrapedContent(
                    url=url,
                    content=content,
                    selector_used=used_selector,
                    title=title,
                    success=True
                )
            else:
                # No selectors - get full body text
                body = soup.find('body')
                content = body.get_text(separator=' ', strip=True) if body else ""
                
                return ScrapedContent(
                    url=url,
                    content=content,
                    selector_used="body",
                    title=title,
                    success=True
                )
                
        except requests.Timeout:
            return ScrapedContent(
                url=url,
                content="",
                success=False,
                error_message=f"Request timed out after {timeout} seconds"
            )
        except requests.RequestException as e:
            return ScrapedContent(
                url=url,
                content="",
                success=False,
                error_message=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return ScrapedContent(
                url=url,
                content="",
                success=False,
                error_message=f"Scraping failed: {str(e)}"
            )
    
    def scrape_multiple(
        self, 
        urls_config: List[Dict[str, Any]]
    ) -> List[ScrapedContent]:
        """
        Scrape multiple URLs with their respective selectors.
        
        Args:
            urls_config: List of dicts with 'url' and optional 'selectors' keys
            
        Returns:
            List of ScrapedContent results
        """
        results = []
        
        for config in urls_config:
            url = config.get('url')
            selectors = config.get('selectors')
            
            if url:
                result = self.scrape_url(url, selectors)
                results.append(result)
        
        return results
    
    def extract_pricing_elements(self, url: str) -> ScrapedContent:
        """
        Specialized method for extracting pricing information.
        Uses common pricing-related selectors.
        """
        pricing_selectors = [
            "#pricing-table",
            ".pricing",
            ".pricing-section",
            ".price",
            ".pricing-card",
            ".plan",
            ".plans",
            "[data-pricing]",
            ".tier",
            ".subscription"
        ]
        return self.scrape_url(url, pricing_selectors)
    
    def extract_feature_elements(self, url: str) -> ScrapedContent:
        """
        Specialized method for extracting feature information.
        Uses common feature-related selectors.
        """
        feature_selectors = [
            "#features",
            ".features",
            ".feature-list",
            ".product-features",
            ".feature-section",
            "[data-features]",
            ".capabilities",
            ".benefits"
        ]
        return self.scrape_url(url, feature_selectors)


# Global scraper instance
scraper_agent = ScraperAgent()
