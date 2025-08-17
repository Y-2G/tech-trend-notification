import logging
from typing import List, Optional
from datetime import datetime
import asyncio

from tavily import TavilyClient

from .base import BaseCollector
from ..models.article import Article
from ..config.settings import settings

logger = logging.getLogger(__name__)


class WebSearchCollector(BaseCollector):
    """Collects articles using Tavily web search API."""
    
    def __init__(self):
        super().__init__("web_search")
        self.client = TavilyClient(api_key=settings.tavily_api_key)
    
    async def collect_articles(self, queries: List[str], max_results: int = 15) -> List[Article]:
        """Collect articles from web search using generated queries."""
        articles = []
        
        for query in queries:
            try:
                query_articles = await self._search_query(query, max_results // len(queries))
                articles.extend(query_articles)
                
                # Respect rate limits
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error searching for query '{query}': {e}")
                continue
        
        # Remove duplicates and limit results
        unique_articles = list({article.url: article for article in articles}.values())
        return unique_articles[:max_results]
    
    async def _search_query(self, query: str, max_results: int) -> List[Article]:
        """Search for a specific query."""
        try:
            # Use asyncio to run the synchronous Tavily client
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results,
                    include_domains=["github.com", "stackoverflow.com", "dev.to", "medium.com", "techcrunch.com"],
                    exclude_domains=["facebook.com", "twitter.com", "instagram.com"]
                )
            )
            
            articles = []
            for result in response.get("results", []):
                try:
                    article = self._create_article_from_result(result, query)
                    if article and self._is_recent_article(article.published_date):
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Error creating article from search result: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Tavily search failed for query '{query}': {e}")
            return []
    
    def _create_article_from_result(self, result: dict, query: str) -> Optional[Article]:
        """Create Article object from Tavily search result."""
        try:
            # Extract published date if available
            published_date = None
            if "published_date" in result:
                try:
                    published_date = datetime.fromisoformat(result["published_date"].replace("Z", "+00:00"))
                except:
                    pass
            
            article = Article(
                title=self._clean_text(result.get("title", "")),
                url=result.get("url", ""),
                content=self._clean_text(result.get("content", "")),
                published_date=published_date,
                source="Tavily Web Search",
                source_type="web_search",
                tags=[query]  # Use search query as initial tag
            )
            
            return article
            
        except Exception as e:
            logger.error(f"Error creating article from result: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if Tavily API is accessible."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(query="test", max_results=1)
            )
            return "results" in response
        except Exception as e:
            logger.error(f"Tavily health check failed: {e}")
            return False