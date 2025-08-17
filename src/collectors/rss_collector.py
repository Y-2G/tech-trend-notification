import logging
import asyncio
from typing import List, Optional
from datetime import datetime
import time

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from models.article import Article

logger = logging.getLogger(__name__)


class RSSCollector(BaseCollector):
    """Collects articles from RSS/Atom feeds."""
    
    def __init__(self):
        super().__init__("rss_feeds")
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'TechTrendNotifier/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def collect_articles(self, feed_urls: List[str]) -> List[Article]:
        """Collect articles from RSS feeds."""
        if not self.session:
            async with self:
                return await self._collect_from_feeds(feed_urls)
        else:
            return await self._collect_from_feeds(feed_urls)
    
    async def _collect_from_feeds(self, feed_urls: List[str]) -> List[Article]:
        """Internal method to collect from feeds."""
        articles = []
        
        # Process feeds concurrently
        tasks = [self._process_feed(url) for url in feed_urls]
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in feed_results:
            if isinstance(result, Exception):
                logger.error(f"Feed processing failed: {result}")
                continue
            articles.extend(result)
        
        # Remove duplicates and limit results
        unique_articles = list({article.url: article for article in articles}.values())
        return unique_articles[:self.max_articles]
    
    async def _process_feed(self, feed_url: str) -> List[Article]:
        """Process a single RSS feed."""
        try:
            # Fetch feed content
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch feed {feed_url}: HTTP {response.status}")
                    return []
                
                content = await response.text()
            
            # Parse feed
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries[:self.max_articles]:
                try:
                    article = self._create_article_from_entry(entry, feed_url)
                    if article and self._is_recent_article(article.published_date):
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Error creating article from feed entry: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error processing RSS feed {feed_url}: {e}")
            return []
    
    def _create_article_from_entry(self, entry, feed_url: str) -> Optional[Article]:
        """Create Article object from RSS feed entry."""
        try:
            # Extract title
            title = self._clean_text(entry.get("title", ""))
            if not title:
                return None
            
            # Extract URL
            url = entry.get("link", "")
            if not url:
                return None
            
            # Extract content
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].value if entry.content else ""
            elif hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description
            
            # Clean HTML from content
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                content = self._clean_text(soup.get_text())
            
            # Extract published date
            published_date = None
            for date_field in ["published_parsed", "updated_parsed"]:
                if hasattr(entry, date_field):
                    date_tuple = getattr(entry, date_field)
                    if date_tuple:
                        try:
                            published_date = datetime(*date_tuple[:6])
                            break
                        except:
                            continue
            
            # Extract author
            author = None
            if hasattr(entry, "author"):
                author = self._clean_text(entry.author)
            
            # Determine source name from feed
            source_name = feed_url
            try:
                from urllib.parse import urlparse
                parsed = urlparse(feed_url)
                source_name = parsed.netloc
            except:
                pass
            
            article = Article(
                title=title,
                url=url,
                content=content,
                author=author,
                published_date=published_date,
                source=source_name,
                source_type="rss"
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Error creating article from RSS entry: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if RSS collector can fetch feeds."""
        test_feed = "https://feeds.feedburner.com/oreilly/radar"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(test_feed, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"RSS health check failed: {e}")
            return False