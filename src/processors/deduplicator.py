import logging
from typing import List, Set
from urllib.parse import urlparse, parse_qs
import hashlib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..models.article import Article
from ..config.settings import settings

logger = logging.getLogger(__name__)


class ArticleDeduplicator:
    """Removes duplicate articles using URL and content similarity."""
    
    def __init__(self, similarity_threshold: float = None):
        self.similarity_threshold = similarity_threshold or settings.similarity_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
    
    def deduplicate_articles(self, articles: List[Article]) -> List[Article]:
        """Remove duplicate articles based on URL and content similarity."""
        if not articles:
            return []
        
        logger.info(f"Deduplicating {len(articles)} articles")
        
        # Step 1: Remove exact URL duplicates
        url_deduplicated = self._remove_url_duplicates(articles)
        logger.info(f"After URL deduplication: {len(url_deduplicated)} articles")
        
        # Step 2: Remove content similarity duplicates
        content_deduplicated = self._remove_content_duplicates(url_deduplicated)
        logger.info(f"After content deduplication: {len(content_deduplicated)} articles")
        
        return content_deduplicated
    
    def _remove_url_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove articles with duplicate URLs."""
        seen_urls: Set[str] = set()
        unique_articles = []
        
        for article in articles:
            normalized_url = self._normalize_url(str(article.url))
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_articles.append(article)
            else:
                logger.debug(f"Removed duplicate URL: {normalized_url}")
        
        return unique_articles
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison by removing tracking parameters."""
        try:
            parsed = urlparse(url)
            
            # Remove common tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'ref', 'source', 'campaign'
            }
            
            query_params = parse_qs(parsed.query)
            filtered_params = {
                k: v for k, v in query_params.items() 
                if k.lower() not in tracking_params
            }
            
            # Reconstruct URL without tracking parameters
            from urllib.parse import urlencode, urlunparse
            clean_query = urlencode(filtered_params, doseq=True)
            
            normalized = urlunparse((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip('/'),
                parsed.params,
                clean_query,
                ''  # Remove fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizing URL {url}: {e}")
            return url.lower()
    
    def _remove_content_duplicates(self, articles: List[Article]) -> List[Article]:
        """Remove articles with similar content using TF-IDF similarity."""
        if len(articles) <= 1:
            return articles
        
        try:
            # Prepare content for similarity analysis
            contents = []
            for article in articles:
                content = self._prepare_content_for_similarity(article)
                contents.append(content)
            
            # Skip similarity analysis if content is too sparse
            if not any(contents) or len([c for c in contents if len(c.split()) > 3]) < 2:
                return articles
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(contents)
            
            # Calculate cosine similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find duplicates
            duplicates_to_remove = set()
            
            for i in range(len(articles)):
                if i in duplicates_to_remove:
                    continue
                
                for j in range(i + 1, len(articles)):
                    if j in duplicates_to_remove:
                        continue
                    
                    similarity = similarity_matrix[i][j]
                    
                    if similarity >= self.similarity_threshold:
                        # Keep the article with more content or better source
                        article_i, article_j = articles[i], articles[j]
                        
                        if self._should_keep_first_article(article_i, article_j):
                            duplicates_to_remove.add(j)
                            logger.debug(f"Removed similar article: {article_j.title[:50]}...")
                        else:
                            duplicates_to_remove.add(i)
                            logger.debug(f"Removed similar article: {article_i.title[:50]}...")
                            break
            
            # Return articles not marked for removal
            unique_articles = [
                article for i, article in enumerate(articles)
                if i not in duplicates_to_remove
            ]
            
            return unique_articles
            
        except Exception as e:
            logger.error(f"Error in content deduplication: {e}")
            # Return original articles if deduplication fails
            return articles
    
    def _prepare_content_for_similarity(self, article: Article) -> str:
        """Prepare article content for similarity analysis."""
        content_parts = []
        
        if article.title:
            content_parts.append(article.title)
        
        if article.content:
            # Limit content length for performance
            content = article.content[:1000]
            content_parts.append(content)
        
        return " ".join(content_parts)
    
    def _should_keep_first_article(self, article1: Article, article2: Article) -> bool:
        """Determine which article to keep when duplicates are found."""
        # Prefer articles with more content
        content1_len = len(article1.content or "")
        content2_len = len(article2.content or "")
        
        if content1_len != content2_len:
            return content1_len > content2_len
        
        # Prefer articles with published dates
        if article1.published_date and not article2.published_date:
            return True
        if article2.published_date and not article1.published_date:
            return False
        
        # Prefer more recent articles
        if article1.published_date and article2.published_date:
            return article1.published_date > article2.published_date
        
        # Prefer articles from certain sources (can be customized)
        preferred_sources = ["github.com", "stackoverflow.com", "dev.to"]
        
        source1_preferred = any(source in article1.source.lower() for source in preferred_sources)
        source2_preferred = any(source in article2.source.lower() for source in preferred_sources)
        
        if source1_preferred and not source2_preferred:
            return True
        if source2_preferred and not source1_preferred:
            return False
        
        # Default: keep first article
        return True