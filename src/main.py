#!/usr/bin/env python3
"""
Tech Trend Notifier - Main Application Entry Point

Collects and curates technology articles from multiple sources,
processes them with AI, and sends notifications to Slack.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List

from config.settings import settings
from config.profile import profile_manager
from config.messages import get_message
from models.article import Article, ProcessedArticleCollection

from collectors.web_search import WebSearchCollector
from collectors.rss_collector import RSSCollector

from processors.query_generator import QueryGenerator
from processors.deduplicator import ArticleDeduplicator
from processors.scorer import ArticleScorer
from processors.summarizer import ArticleSummarizer

from notifiers.slack_notifier import SlackNotifier

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tech_trends.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


class TechTrendNotifier:
    """Main application class for tech trend collection and notification."""
    
    def __init__(self):
        self.profile = profile_manager.profile
        self.query_generator = QueryGenerator()
        self.deduplicator = ArticleDeduplicator()
        self.scorer = ArticleScorer()
        self.summarizer = ArticleSummarizer()
        self.slack_notifier = SlackNotifier()
        
        # Initialize collectors
        self.collectors = {}
        if self.profile.sources.web_search.enabled:
            self.collectors['web_search'] = WebSearchCollector()
        if self.profile.sources.rss_feeds.enabled:
            self.collectors['rss_feeds'] = RSSCollector()
    
    async def run_weekly_collection(self) -> bool:
        """Run the complete weekly collection and notification process."""
        logger.info("Starting weekly tech trend collection")
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Generate search queries
            logger.info("Generating search queries...")
            queries = await self.query_generator.generate_search_queries()
            logger.info(f"Generated {len(queries)} search queries")
            
            # Step 2: Collect articles from all sources
            logger.info("Collecting articles from sources...")
            all_articles = await self._collect_from_all_sources(queries)
            logger.info(f"Collected {len(all_articles)} articles total")
            
            if not all_articles:
                logger.warning("No articles collected, sending empty notification")
                await self.slack_notifier.send_weekly_summary([], get_message("no_articles"))
                return True
            
            # Step 3: Deduplicate articles
            logger.info("Deduplicating articles...")
            unique_articles = self.deduplicator.deduplicate_articles(all_articles)
            logger.info(f"After deduplication: {len(unique_articles)} unique articles")
            
            # Step 4: Score articles for relevance
            logger.info("Scoring articles for relevance...")
            scored_articles = self.scorer.score_articles(unique_articles)
            
            # Step 5: Summarize top articles
            logger.info("Generating article summaries...")
            top_articles = scored_articles[:20]  # Summarize top 20
            await self.summarizer.summarize_articles(top_articles)
            
            # Step 6: Generate collection summary
            logger.info("Generating collection overview...")
            collection_summary = await self.summarizer.generate_collection_summary(scored_articles)
            
            # Step 7: Send Slack notification
            logger.info("Sending Slack notification...")
            notification_sent = await self.slack_notifier.send_weekly_summary(
                scored_articles, collection_summary
            )
            
            # Log completion
            duration = datetime.utcnow() - start_time
            logger.info(f"Weekly collection completed in {duration.total_seconds():.1f} seconds")
            logger.info(f"Final stats: {len(scored_articles)} articles, notification sent: {notification_sent}")
            
            return notification_sent
            
        except Exception as e:
            logger.error(f"Error during weekly collection: {e}", exc_info=True)
            
            # Send error notification
            try:
                await self.slack_notifier.send_error_notification(str(e))
            except Exception as notify_error:
                logger.error(f"Failed to send error notification: {notify_error}")
            
            return False
    
    async def _collect_from_all_sources(self, queries: List[str]) -> List[Article]:
        """Collect articles from all enabled sources."""
        all_articles = []
        
        # Collect from web search
        if 'web_search' in self.collectors:
            try:
                web_articles = await self.collectors['web_search'].collect_articles(
                    queries, self.profile.sources.web_search.max_results
                )
                all_articles.extend(web_articles)
                logger.info(f"Web search collected {len(web_articles)} articles")
            except Exception as e:
                logger.error(f"Web search collection failed: {e}")
        
        # Collect from RSS feeds
        if 'rss_feeds' in self.collectors:
            try:
                async with self.collectors['rss_feeds'] as rss_collector:
                    rss_articles = await rss_collector.collect_articles(
                        self.profile.sources.rss_feeds.feeds
                    )
                    all_articles.extend(rss_articles)
                    logger.info(f"RSS feeds collected {len(rss_articles)} articles")
            except Exception as e:
                logger.error(f"RSS collection failed: {e}")
        
        return all_articles
    
    async def health_check(self) -> bool:
        """Perform health check on all components."""
        logger.info("Performing system health check...")
        
        checks = {
            'slack': await self.slack_notifier.test_connection(),
        }
        
        # Check collectors
        for name, collector in self.collectors.items():
            checks[name] = await collector.health_check()
        
        # Log results
        for component, status in checks.items():
            status_str = "✅ OK" if status else "❌ FAILED"
            logger.info(f"{component}: {status_str}")
        
        all_healthy = all(checks.values())
        logger.info(f"Overall health: {'✅ HEALTHY' if all_healthy else '❌ ISSUES DETECTED'}")
        
        return all_healthy
    
    async def test_run(self) -> bool:
        """Run a test collection with limited scope."""
        logger.info("Running test collection...")
        
        try:
            # Generate fewer queries for testing
            queries = await self.query_generator.generate_search_queries(max_queries=2)
            
            # Collect limited articles
            if 'web_search' in self.collectors:
                articles = await self.collectors['web_search'].collect_articles(queries, 5)
                logger.info(f"Test collected {len(articles)} articles")
                
                if articles:
                    # Quick processing
                    scored_articles = self.scorer.score_articles(articles)
                    logger.info("Test processing completed successfully")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Test run failed: {e}")
            return False


async def main():
    """Main entry point."""
    logger.info("Tech Trend Notifier starting...")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Tech Trend Notifier')
    parser.add_argument('--test', action='store_true', help='Run test collection')
    parser.add_argument('--health', action='store_true', help='Run health check')
    args = parser.parse_args()
    
    # Initialize application
    app = TechTrendNotifier()
    
    try:
        if args.health:
            # Health check mode
            healthy = await app.health_check()
            sys.exit(0 if healthy else 1)
        
        elif args.test:
            # Test mode
            success = await app.test_run()
            sys.exit(0 if success else 1)
        
        else:
            # Normal weekly collection
            success = await app.run_weekly_collection()
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())