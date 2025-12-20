"""
Data Extraction Agent
Extracts and structures data from scraped content.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from bs4 import BeautifulSoup


@dataclass
class PricingInfo:
    """Extracted pricing information."""
    plan_name: str
    price: Optional[str] = None
    billing_period: Optional[str] = None
    features: List[str] = field(default_factory=list)
    currency: Optional[str] = None


@dataclass
class FeatureInfo:
    """Extracted feature information."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_new: bool = False


@dataclass 
class ExtractedData:
    """Container for all extracted data."""
    url: str
    pricing: List[PricingInfo] = field(default_factory=list)
    features: List[FeatureInfo] = field(default_factory=list)
    marketing_claims: List[str] = field(default_factory=list)
    raw_text: str = ""


class ExtractorAgent:
    """
    Agent for extracting structured data from HTML content.
    Focuses on pricing, features, and marketing elements.
    """
    
    def __init__(self):
        """Initialize extractor with common patterns."""
        self.price_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:/)?(?:mo|month|yr|year))?',
            r'€[\d,]+(?:\.\d{2})?(?:\s*(?:/)?(?:mo|month|yr|year))?',
            r'£[\d,]+(?:\.\d{2})?(?:\s*(?:/)?(?:mo|month|yr|year))?',
            r'[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP)',
        ]
        self.compiled_price_patterns = [re.compile(p, re.IGNORECASE) for p in self.price_patterns]
    
    def extract_from_html(self, html: str, url: str) -> ExtractedData:
        """
        Extract structured data from HTML content.
        
        Args:
            html: Raw HTML content
            url: The source URL
            
        Returns:
            ExtractedData with pricing, features, and marketing info
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = ExtractedData(
            url=url,
            raw_text=soup.get_text(separator=' ', strip=True)
        )
        
        # Extract pricing
        result.pricing = self._extract_pricing(soup)
        
        # Extract features
        result.features = self._extract_features(soup)
        
        # Extract marketing claims
        result.marketing_claims = self._extract_marketing_claims(soup)
        
        return result
    
    def extract_from_text(self, text: str, url: str) -> ExtractedData:
        """
        Extract structured data from plain text content.
        
        Args:
            text: Plain text content
            url: The source URL
            
        Returns:
            ExtractedData with extracted information
        """
        result = ExtractedData(url=url, raw_text=text)
        
        # Extract prices from text
        prices = self._find_prices_in_text(text)
        for price in prices:
            result.pricing.append(PricingInfo(
                plan_name="Unknown",
                price=price
            ))
        
        return result
    
    def _extract_pricing(self, soup: BeautifulSoup) -> List[PricingInfo]:
        """Extract pricing information from HTML."""
        pricing = []
        
        # Look for pricing containers
        pricing_selectors = [
            '.pricing-card', '.price-card', '.plan-card',
            '.pricing-tier', '.plan', '.tier',
            '[data-pricing]', '[data-plan]'
        ]
        
        for selector in pricing_selectors:
            cards = soup.select(selector)
            for card in cards:
                info = self._parse_pricing_card(card)
                if info:
                    pricing.append(info)
        
        return pricing
    
    def _parse_pricing_card(self, element) -> Optional[PricingInfo]:
        """Parse a single pricing card element."""
        # Try to find plan name
        name_selectors = ['.plan-name', '.tier-name', 'h2', 'h3', '.title']
        plan_name = None
        for sel in name_selectors:
            name_elem = element.select_one(sel)
            if name_elem:
                plan_name = name_elem.get_text(strip=True)
                break
        
        if not plan_name:
            plan_name = "Unknown Plan"
        
        # Try to find price
        price = None
        price_elem = element.select_one('.price, .amount, [data-price]')
        if price_elem:
            price = price_elem.get_text(strip=True)
        else:
            # Try to find price in text
            card_text = element.get_text()
            prices = self._find_prices_in_text(card_text)
            if prices:
                price = prices[0]
        
        # Extract features list
        features = []
        feature_list = element.select('li, .feature, .benefit')
        for feat in feature_list[:10]:  # Limit to 10 features
            feat_text = feat.get_text(strip=True)
            if feat_text and len(feat_text) < 200:
                features.append(feat_text)
        
        return PricingInfo(
            plan_name=plan_name,
            price=price,
            features=features
        )
    
    def _extract_features(self, soup: BeautifulSoup) -> List[FeatureInfo]:
        """Extract feature information from HTML."""
        features = []
        
        feature_selectors = [
            '.feature', '.feature-item', '.product-feature',
            '[data-feature]', '.capability'
        ]
        
        for selector in feature_selectors:
            elements = soup.select(selector)
            for elem in elements:
                name = elem.get_text(strip=True)[:100]
                if name:
                    # Check if marked as new
                    is_new = bool(elem.select_one('.new, .badge-new, [data-new]'))
                    features.append(FeatureInfo(
                        name=name,
                        is_new=is_new
                    ))
        
        return features[:20]  # Limit results
    
    def _extract_marketing_claims(self, soup: BeautifulSoup) -> List[str]:
        """Extract marketing claims and headlines."""
        claims = []
        
        # Look for headlines and taglines
        headline_selectors = ['h1', '.hero-title', '.tagline', '.headline', '.value-prop']
        
        for selector in headline_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and 10 < len(text) < 200:
                    claims.append(text)
        
        return claims[:10]  # Limit results
    
    def _find_prices_in_text(self, text: str) -> List[str]:
        """Find all price mentions in text."""
        prices = []
        for pattern in self.compiled_price_patterns:
            matches = pattern.findall(text)
            prices.extend(matches)
        return list(set(prices))  # Remove duplicates


# Global extractor instance
extractor_agent = ExtractorAgent()
