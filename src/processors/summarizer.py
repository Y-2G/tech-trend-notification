import logging
from typing import List, Optional
import asyncio

import openai

from models.article import Article
from config.settings import settings

logger = logging.getLogger(__name__)


class ArticleSummarizer:
    """Summarizes articles using OpenAI GPT for better readability."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.max_concurrent = 5  # Limit concurrent API calls
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def summarize_articles(self, articles: List[Article]) -> List[Article]:
        """Summarize multiple articles concurrently."""
        # Only summarize articles that don't already have summaries
        articles_to_summarize = [
            article for article in articles 
            if not article.summary and article.content
        ]
        
        if not articles_to_summarize:
            return articles
        
        logger.info(f"Summarizing {len(articles_to_summarize)} articles")
        
        # Process articles in batches to respect rate limits
        batch_size = 10
        for i in range(0, len(articles_to_summarize), batch_size):
            batch = articles_to_summarize[i:i + batch_size]
            
            # Create summarization tasks
            tasks = [self._summarize_single_article(article) for article in batch]
            
            # Execute batch with rate limiting
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay between batches
            if i + batch_size < len(articles_to_summarize):
                await asyncio.sleep(1.0)
        
        return articles
    
    async def _summarize_single_article(self, article: Article) -> None:
        """Summarize a single article."""
        async with self.semaphore:
            try:
                summary = await self._generate_summary(article)
                if summary:
                    article.summary = summary
                    logger.debug(f"Summarized: {article.title[:50]}...")
                
            except Exception as e:
                logger.error(f"Error summarizing article '{article.title[:50]}...': {e}")
                # Create a fallback summary from the beginning of content
                article.summary = self._create_fallback_summary(article.content)
    
    async def _generate_summary(self, article: Article) -> Optional[str]:
        """Generate summary using OpenAI GPT."""
        if not article.content:
            return None
        
        # Limit content length for API efficiency
        content = article.content[:2000]  # Limit to ~2000 chars
        
        prompt = f"""
        Summarize this technical article in 2-3 sentences. Focus on:
        - Key technical points and innovations
        - Practical implications for developers
        - Important updates or changes mentioned
        
        Title: {article.title}
        Content: {content}
        
        Summary:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a technical writer who creates concise, informative summaries of technology articles. Focus on practical information that developers would find useful."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Validate summary quality
            if self._is_valid_summary(summary, article.title):
                return summary
            else:
                logger.warning(f"Generated summary failed validation for: {article.title[:50]}...")
                return self._create_fallback_summary(content)
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._create_fallback_summary(content)
    
    def _is_valid_summary(self, summary: str, title: str) -> bool:
        """Validate that the generated summary is useful."""
        if not summary or len(summary.strip()) < 20:
            return False
        
        # Check if summary is too generic
        generic_phrases = [
            "this article discusses",
            "the article talks about",
            "this post covers",
            "the author explains"
        ]
        
        summary_lower = summary.lower()
        if any(phrase in summary_lower for phrase in generic_phrases):
            return False
        
        # Check if summary has some relation to the title
        title_words = set(title.lower().split())
        summary_words = set(summary.lower().split())
        
        # Should have at least some word overlap
        overlap = len(title_words.intersection(summary_words))
        if overlap == 0 and len(title_words) > 2:
            return False
        
        return True
    
    def _create_fallback_summary(self, content: str) -> str:
        """Create a simple fallback summary from content."""
        if not content:
            return "No summary available."
        
        # Take first few sentences
        sentences = content.split('.')[:3]
        summary = '. '.join(sentence.strip() for sentence in sentences if sentence.strip())
        
        # Limit length
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        return summary if summary else "Content available - summary generation failed."
    
    async def generate_collection_summary(self, articles: List[Article]) -> str:
        """Generate a summary of the entire article collection."""
        if not articles:
            return "No articles collected this week."
        
        # Get top articles for summary
        top_articles = sorted(articles, key=lambda x: x.score or 0, reverse=True)[:5]
        
        # Create overview of topics
        all_tags = []
        for article in articles:
            all_tags.extend(article.tags)
        
        # Count tag frequency
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_topics = [tag for tag, count in tag_counts.most_common(5)]
        
        prompt = f"""
        Create a brief overview of this week's tech trends based on {len(articles)} collected articles.
        
        Top topics: {', '.join(top_topics)}
        
        Top articles:
        {chr(10).join([f"- {article.title}" for article in top_articles[:3]])}
        
        Write 2-3 sentences highlighting the main themes and important developments.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a tech trend analyst. Create concise overviews of weekly technology developments."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating collection summary: {e}")
            return f"Collected {len(articles)} articles covering topics like {', '.join(top_topics[:3])}."