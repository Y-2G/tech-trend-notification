import logging
from typing import List, Dict, Any
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..models.article import Article
from ..config.settings import settings
from ..config.profile import profile_manager

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Sends formatted notifications to Slack using Block Kit."""
    
    def __init__(self):
        self.client = WebClient(token=settings.slack_bot_token)
        self.channel = settings.slack_channel
        self.profile = profile_manager.profile
    
    async def send_weekly_summary(self, articles: List[Article], collection_summary: str = "") -> bool:
        """Send weekly tech trends summary to Slack."""
        try:
            # Limit articles based on configuration
            max_articles = self.profile.notification.slack.max_articles
            top_articles = articles[:max_articles]
            
            # Create message blocks
            blocks = self._create_summary_blocks(top_articles, collection_summary)
            
            # Send message
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"Weekly Tech Trends - {len(top_articles)} articles"  # Fallback text
            )
            
            if response["ok"]:
                logger.info(f"Successfully sent weekly summary to Slack with {len(top_articles)} articles")
                return True
            else:
                logger.error(f"Slack API returned error: {response}")
                return False
                
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def _create_summary_blocks(self, articles: List[Article], collection_summary: str) -> List[Dict[str, Any]]:
        """Create Slack Block Kit blocks for the weekly summary."""
        blocks = []
        
        # Header block
        header_text = f"📈 *Weekly Tech Trends* - {datetime.now().strftime('%B %d, %Y')}"
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Weekly Tech Trends"
            }
        })
        
        # Collection summary if available
        if collection_summary:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*This Week's Overview:*\n{collection_summary}"
                }
            })
            blocks.append({"type": "divider"})
        
        # Articles summary
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📊 *{len(articles)} articles collected* from multiple sources"
            }
        })
        
        # Top articles
        if articles:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*🔥 Top Articles:*"
                }
            })
            
            for i, article in enumerate(articles[:10], 1):  # Show top 10
                article_block = self._create_article_block(article, i)
                blocks.extend(article_block)
        
        # Footer with stats
        if len(articles) > 10:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Showing top 10 of {len(articles)} articles. Full list available in detailed report._"
                    }
                ]
            })
        
        # Add timestamp
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}_"
                }
            ]
        })
        
        return blocks
    
    def _create_article_block(self, article: Article, index: int) -> List[Dict[str, Any]]:
        """Create blocks for a single article."""
        blocks = []
        
        # Article title and link
        title_text = f"*{index}. <{article.url}|{article.title}>*"
        
        # Add score if enabled
        if self.profile.notification.slack.include_score and article.score:
            score_emoji = self._get_score_emoji(article.score)
            title_text += f" {score_emoji} _{article.score:.2f}_"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title_text
            }
        })
        
        # Article details
        details = []
        
        if article.source:
            details.append(f"📰 {article.source}")
        
        if article.published_date:
            date_str = article.published_date.strftime("%b %d")
            details.append(f"📅 {date_str}")
        
        if article.tags:
            tags_str = " ".join([f"`{tag}`" for tag in article.tags[:3]])
            details.append(f"🏷️ {tags_str}")
        
        if details:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": " • ".join(details)
                    }
                ]
            })
        
        # Article summary if enabled and available
        if (self.profile.notification.slack.include_summary and 
            article.summary and len(article.summary.strip()) > 0):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_{article.summary}_"
                }
            })
        
        # Add small divider between articles (except for last one)
        blocks.append({"type": "divider"})
        
        return blocks
    
    def _get_score_emoji(self, score: float) -> str:
        """Get emoji representation of article score."""
        if score >= 0.8:
            return "🔥"
        elif score >= 0.6:
            return "⭐"
        elif score >= 0.4:
            return "👍"
        else:
            return "📄"
    
    async def send_error_notification(self, error_message: str) -> bool:
        """Send error notification to Slack."""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ Tech Trends Collection Error"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error occurred during weekly collection:*\n```{error_message}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Time: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_"
                        }
                    ]
                }
            ]
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text="Tech Trends Collection Error"
            )
            
            return response["ok"]
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Slack connection and permissions."""
        try:
            # Test auth
            auth_response = self.client.auth_test()
            if not auth_response["ok"]:
                logger.error("Slack auth test failed")
                return False
            
            # Test channel access
            channel_info = self.client.conversations_info(channel=self.channel)
            if not channel_info["ok"]:
                logger.error(f"Cannot access Slack channel: {self.channel}")
                return False
            
            logger.info("Slack connection test successful")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack connection test failed: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Slack connection test error: {e}")
            return False