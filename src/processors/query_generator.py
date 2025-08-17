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
        
        prompt = f"""
        Generate {max_queries} specific search queries for finding recent technology articles and trends.
        
        User interests: {interests_str}
        High priority keywords: {high_priority_keywords}
        
        Focus on:
        - Recent developments and updates (last 7 days)
        - Breaking news in technology
        - New releases and announcements
        - Security vulnerabilities and fixes
        - Performance improvements and optimizations
        
        Return only the search queries, one per line, without numbering or additional text.
        Make queries specific and likely to find high-quality technical content.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a tech trend analyst. Generate precise search queries for finding the latest technology news and developments."},
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
        """Generate default search queries based on interests."""
        base_queries = [
            "latest technology news this week",
            "new software releases 2024",
            "tech security vulnerabilities",
            "programming language updates",
            "cloud computing trends"
        ]
        
        # Add interest-specific queries
        interest_queries = []
        for interest in interests[:3]:  # Limit to top 3 interests
            interest_queries.append(f"{interest} latest news")
            interest_queries.append(f"{interest} new features 2024")
        
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