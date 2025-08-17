import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta

from ..models.article import Article
from ..config.settings import settings

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for all content collectors."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.max_articles = settings.max_articles_per_source
        self.rate_limit = settings.api_rate_limit
        self._semaphore = asyncio.Semaphore(self.rate_limit)
    
    @abstractmethod
    async def collect_articles(self, **kwargs) -> List[Article]:
        """Collect articles from the source."""
        pass
    
    async def _rate_limited_request(self, coro):
        """Execute coroutine with rate limiting."""
        async with self._semaphore:
            try:
                result = await coro
                # Small delay to respect rate limits
                await asyncio.sleep(1.0 / self.rate_limit)
                return result
            except Exception as e:
                logger.error(f"Rate limited request failed for {self.source_name}: {e}")
                raise
    
    def _is_recent_article(self, published_date: Optional[datetime], days: int = 7) -> bool:
        """Check if article was published within the specified days."""
        if not published_date:
            return True  # Include articles without date
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return published_date >= cutoff_date
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = " ".join(text.split())
        return cleaned.strip()
    
    def _extract_tags(self, content: str, interests: List[str]) -> List[str]:
        """Extract relevant tags from content based on interests."""
        if not content:
            return []
        
        content_lower = content.lower()
        found_tags = []
        
        for interest in interests:
            if interest.lower() in content_lower:
                found_tags.append(interest)
        
        return found_tags
    
    async def health_check(self) -> bool:
        """Check if the collector can connect to its data source."""
        try:
            # Override in subclasses for specific health checks
            return True
        except Exception as e:
            logger.error(f"Health check failed for {self.source_name}: {e}")
            return False