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
        
        # Language-specific prompt
        if settings.language == "ja":
            prompt = f"""
            以下の技術記事を日本語で2-3文で要約してください。記事が英語で書かれていても、必ず日本語で要約してください。
            
            以下に焦点を当ててください:
            - 主要な技術的ポイントと革新
            - 開発者への実用的な影響
            - 言及されている重要なアップデートや変更
            
            記事タイトル: {article.title}
            記事内容: {content}
            
            日本語要約:
            """
        else:
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
            # Language-specific system message
            if settings.language == "ja":
                system_message = "あなたは技術記事の簡潔で有益な日本語要約を作成するテクニカルライターです。英語の記事でも必ず日本語で要約してください。開発者にとって有用な実用的な情報に焦点を当て、専門用語は適切に日本語化または併記してください。"
            else:
                system_message = "You are a technical writer who creates concise, informative summaries of technology articles. Focus on practical information that developers would find useful."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
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
        
        # Language-specific generic phrase detection
        if settings.language == "ja":
            generic_phrases = [
                "この記事では",
                "この記事について",
                "この投稿では",
                "著者は説明",
                "記事では説明",
                "について説明している",
                "について述べている"
            ]
        else:
            generic_phrases = [
                "this article discusses",
                "the article talks about",
                "this post covers",
                "the author explains"
            ]
        
        summary_lower = summary.lower()
        if any(phrase in summary_lower for phrase in generic_phrases):
            return False
        
        # For Japanese, check if the summary contains some Japanese characters
        if settings.language == "ja":
            import re
            # Check if summary contains Japanese characters (hiragana, katakana, kanji)
            japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
            if not japanese_pattern.search(summary):
                logger.warning(f"Summary doesn't contain Japanese characters: {summary[:50]}...")
                return False
        
        # Check if summary has some relation to the title
        title_words = set(title.lower().split())
        summary_words = set(summary.lower().split())
        
        # Should have at least some word overlap (more lenient for Japanese)
        overlap = len(title_words.intersection(summary_words))
        min_overlap = 0 if settings.language == "ja" else 0
        if overlap < min_overlap and len(title_words) > 2:
            return False
        
        return True
    
    def _create_fallback_summary(self, content: str) -> str:
        """Create a simple fallback summary from content."""
        if not content:
            if settings.language == "ja":
                return "要約がありません。"
            else:
                return "No summary available."
        
        # Take first few sentences
        sentences = content.split('.')[:3]
        summary = '. '.join(sentence.strip() for sentence in sentences if sentence.strip())
        
        # Limit length
        if len(summary) > 200:
            summary = summary[:200] + "..."
        
        # For Japanese, add a note that this is a fallback
        if settings.language == "ja":
            fallback_msg = "（自動要約が利用できないため、記事の冒頭部分を表示しています）"
            if summary:
                return f"{summary} {fallback_msg}"
            else:
                return "コンテンツあり - 要約生成に失敗しました。"
        else:
            fallback_msg = "Content available - summary generation failed."
            return summary if summary else fallback_msg
    
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
        
        # Language-specific prompt for collection summary
        if settings.language == "ja":
            prompt = f"""
            収集した{len(articles)}記事に基づいて、今週の技術トレンドの簡潔な概要を日本語で作成してください。
            
            主要トピック: {', '.join(top_topics)}
            
            注目記事:
            {chr(10).join([f"- {article.title}" for article in top_articles[:3]])}
            
            AI自動化、エンジニアリング自動化、MLOps、DevOpsの観点から、主要なテーマと重要な開発動向を強調した2-3文を日本語で書いてください。
            開発者にとって実用的で価値のある情報に焦点を当ててください。
            """
        else:
            prompt = f"""
            Create a brief overview of this week's tech trends based on {len(articles)} collected articles.
            
            Top topics: {', '.join(top_topics)}
            
            Top articles:
            {chr(10).join([f"- {article.title}" for article in top_articles[:3]])}
            
            Write 2-3 sentences highlighting the main themes and important developments.
            """
        
        try:
            # Language-specific system message for collection summary
            if settings.language == "ja":
                system_message = "あなたは技術トレンドアナリストです。AI自動化とエンジニアリング自動化に特化した週間の技術開発動向の簡潔な概要を日本語で作成してください。開発者にとって実用的で価値のある洞察を提供してください。"
            else:
                system_message = "You are a tech trend analyst. Create concise overviews of weekly technology developments."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating collection summary: {e}")
            if settings.language == "ja":
                return f"{len(articles)}記事を収集しました。主なトピック: {', '.join(top_topics[:3])}"
            else:
                return f"Collected {len(articles)} articles covering topics like {', '.join(top_topics[:3])}."