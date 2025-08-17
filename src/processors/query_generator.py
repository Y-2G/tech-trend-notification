import logging
from typing import List
import asyncio

import openai

from config.settings import settings
from config.profile import profile_manager

logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates search queries using OpenAI GPT for content collection."""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_search_queries(self, max_queries: int = 5) -> List[str]:
        """Generate search queries based on user interests and current tech trends."""
        profile = profile_manager.profile
        
        # Create prompt based on user interests
        interests_str = ", ".join(profile.interests)
        high_priority_keywords = ", ".join(profile.keywords.high_priority)
        
        # Create language-specific prompt with strong emphasis on recent content
        if settings.language == "ja":
            prompt = f"""
            過去1週間以内の最新技術記事やトレンドを見つけるための具体的な検索クエリを{max_queries}個生成してください。
            
            ユーザーの関心分野: {interests_str}
            優先度の高いキーワード: {high_priority_keywords}
            
            重要: 必ず過去7日間以内の最新情報に焦点を当ててください:
            - 今週の技術ニュース
            - 最新のリリース・アップデート（2025年8月）
            - 直近のセキュリティ脆弱性と修正
            - 最新のパフォーマンス改善
            - 今週発表された新機能・ツール
            
            各クエリに「最新」「今週」「2025年8月」「最近」などの時間を示すキーワードを含めてください。
            検索クエリのみを1行に1つずつ、番号付けや追加テキストなしで返してください。
            """
        else:
            prompt = f"""
            Generate {max_queries} specific search queries for finding the most recent technology articles and trends from the past week only.
            
            User interests: {interests_str}
            High priority keywords: {high_priority_keywords}
            
            IMPORTANT: Focus exclusively on content from the last 7 days:
            - This week's tech news
            - Latest releases and updates (August 2025)
            - Recent security vulnerabilities and fixes
            - Latest performance improvements
            - New features and tools announced this week
            
            Include time-specific keywords like "latest", "this week", "August 2025", "recent" in each query.
            Return only the search queries, one per line, without numbering or additional text.
            """
        
        try:
            # Language-specific system message
            if settings.language == "ja":
                system_message = "あなたは技術トレンドアナリストです。最新の技術ニュースや開発動向を見つけるための正確な検索クエリを生成してください。"
            else:
                system_message = "You are a tech trend analyst. Generate precise search queries for finding the latest technology news and developments."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            queries = [q.strip() for q in content.split('\n') if q.strip()]
            
            # Ensure we have at least some default queries
            if not queries:
                queries = self._get_default_queries(profile.interests)
            
            return queries[:max_queries]
            
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            # Fallback to default queries
            return self._get_default_queries(profile.interests)[:max_queries]
    
    def _get_default_queries(self, interests: List[str]) -> List[str]:
        """Generate default search queries based on interests with recent date focus."""
        if settings.language == "ja":
            base_queries = [
                "今週の最新技術ニュース",
                "2025年8月 新しいソフトウェアリリース",
                "最新のセキュリティ脆弱性",
                "プログラミング言語 最新アップデート",
                "クラウドコンピューティング 最新トレンド"
            ]
        else:
            base_queries = [
                "latest technology news this week August 2025",
                "new software releases August 2025",
                "recent tech security vulnerabilities",
                "programming language updates this week",
                "cloud computing trends August 2025"
            ]
        
        # Add interest-specific queries with date focus
        interest_queries = []
        for interest in interests[:3]:  # Limit to top 3 interests
            if settings.language == "ja":
                interest_queries.append(f"{interest} 最新ニュース 今週")
                interest_queries.append(f"{interest} 新機能 2025年8月")
            else:
                interest_queries.append(f"{interest} latest news this week")
                interest_queries.append(f"{interest} new features August 2025")
        
        return base_queries + interest_queries
    
    async def enhance_query_with_context(self, base_query: str, context: str = "") -> str:
        """Enhance a search query with additional context."""
        if not context:
            return base_query
        
        prompt = f"""
        Improve this search query to be more specific and effective:
        Base query: {base_query}
        Additional context: {context}
        
        Return only the improved query, nothing else.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a search query optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            enhanced_query = response.choices[0].message.content.strip()
            return enhanced_query if enhanced_query else base_query
            
        except Exception as e:
            logger.error(f"Error enhancing query: {e}")
            return base_query