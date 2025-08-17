import logging
from typing import List, Dict
import re

from models.article import Article
from config.profile import profile_manager

logger = logging.getLogger(__name__)


class ArticleScorer:
    """Scores articles based on relevance to user interests and content quality."""
    
    def __init__(self):
        self.profile = profile_manager.profile
    
    def score_articles(self, articles: List[Article]) -> List[Article]:
        """Score all articles and update their score field."""
        for article in articles:
            article.relevance_score = self._calculate_relevance_score(article)
            article.score = self._calculate_overall_score(article)
        
        # Sort articles by score (highest first)
        articles.sort(key=lambda x: x.score or 0, reverse=True)
        
        return articles
    
    def _calculate_relevance_score(self, article: Article) -> float:
        """Calculate relevance score based on user interests and keywords."""
        score = 0.0
        content_text = self._get_searchable_content(article).lower()
        
        # Score based on interests
        interests_score = self._score_interests(content_text)
        score += interests_score * 0.4
        
        # Score based on keywords
        keywords_score = self._score_keywords(content_text)
        score += keywords_score * 0.3
        
        # Score based on source quality
        source_score = self._score_source(article.source)
        score += source_score * 0.2
        
        # Score based on recency
        recency_score = self._score_recency(article)
        score += recency_score * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_overall_score(self, article: Article) -> float:
        """Calculate overall article score combining relevance and quality metrics."""
        relevance = article.relevance_score or 0.0
        
        # Quality indicators
        quality_score = 0.0
        
        # Title quality (not too short, not too long, descriptive)
        title_score = self._score_title_quality(article.title)
        quality_score += title_score * 0.3
        
        # Content length (prefer substantial content)
        content_score = self._score_content_length(article.content)
        quality_score += content_score * 0.2
        
        # Author presence (articles with authors tend to be higher quality)
        author_score = 0.1 if article.author else 0.0
        quality_score += author_score
        
        # Published date presence
        date_score = 0.1 if article.published_date else 0.0
        quality_score += date_score
        
        # Combine relevance and quality
        overall_score = (relevance * 0.7) + (quality_score * 0.3)
        
        return min(overall_score, 1.0)
    
    def _get_searchable_content(self, article: Article) -> str:
        """Get all searchable text from article."""
        content_parts = []
        
        if article.title:
            content_parts.append(article.title)
        
        if article.content:
            content_parts.append(article.content)
        
        if article.tags:
            content_parts.extend(article.tags)
        
        return " ".join(content_parts)
    
    def _score_interests(self, content: str) -> float:
        """Score based on user interests."""
        if not self.profile.interests:
            return 0.5  # Neutral score if no interests defined
        
        matches = 0
        total_interests = len(self.profile.interests)
        
        for interest in self.profile.interests:
            if interest.lower() in content:
                matches += 1
        
        return matches / total_interests if total_interests > 0 else 0.0
    
    def _score_keywords(self, content: str) -> float:
        """Score based on keyword priorities."""
        score = 0.0
        
        # High priority keywords
        high_priority = self.profile.keywords.high_priority
        for keyword in high_priority:
            if keyword.lower() in content:
                score += 0.3  # High boost for priority keywords
        
        # Medium priority keywords
        medium_priority = self.profile.keywords.medium_priority
        for keyword in medium_priority:
            if keyword.lower() in content:
                score += 0.1  # Medium boost
        
        # Penalty for excluded keywords
        exclude_keywords = self.profile.keywords.exclude
        for keyword in exclude_keywords:
            if keyword.lower() in content:
                score -= 0.2  # Penalty for excluded content
        
        return max(score, 0.0)  # Don't go below 0
    
    def _score_source(self, source: str) -> float:
        """Score based on source quality and reputation."""
        source_lower = source.lower()
        
        # High-quality tech sources
        high_quality_sources = [
            'github.com', 'stackoverflow.com', 'dev.to', 'medium.com',
            'techcrunch.com', 'oreilly.com', 'hacker news', 'reddit.com/r/programming'
        ]
        
        # Medium-quality sources
        medium_quality_sources = [
            'blog', 'news', 'official', 'documentation', 'docs'
        ]
        
        # Check for high-quality sources
        for high_source in high_quality_sources:
            if high_source in source_lower:
                return 1.0
        
        # Check for medium-quality sources
        for medium_source in medium_quality_sources:
            if medium_source in source_lower:
                return 0.7
        
        return 0.5  # Default score for unknown sources
    
    def _score_recency(self, article: Article) -> float:
        """Score based on article recency."""
        if not article.published_date:
            return 0.5  # Neutral score for unknown dates
        
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        age = now - article.published_date
        
        # Prefer very recent articles
        if age <= timedelta(days=1):
            return 1.0
        elif age <= timedelta(days=3):
            return 0.8
        elif age <= timedelta(days=7):
            return 0.6
        elif age <= timedelta(days=14):
            return 0.4
        else:
            return 0.2
    
    def _score_title_quality(self, title: str) -> float:
        """Score title quality based on length and content."""
        if not title:
            return 0.0
        
        title_len = len(title)
        
        # Optimal title length
        if 30 <= title_len <= 100:
            length_score = 1.0
        elif 20 <= title_len <= 120:
            length_score = 0.8
        elif 10 <= title_len <= 150:
            length_score = 0.6
        else:
            length_score = 0.3
        
        # Check for clickbait indicators
        clickbait_patterns = [
            r'\d+\s+(things|ways|reasons|tips)',
            r'you won\'t believe',
            r'shocking',
            r'amazing',
            r'incredible'
        ]
        
        clickbait_penalty = 0.0
        for pattern in clickbait_patterns:
            if re.search(pattern, title.lower()):
                clickbait_penalty += 0.2
        
        return max(length_score - clickbait_penalty, 0.0)
    
    def _score_content_length(self, content: str) -> float:
        """Score based on content length (prefer substantial content)."""
        if not content:
            return 0.0
        
        content_len = len(content)
        
        if content_len >= 1000:
            return 1.0
        elif content_len >= 500:
            return 0.8
        elif content_len >= 200:
            return 0.6
        elif content_len >= 100:
            return 0.4
        else:
            return 0.2