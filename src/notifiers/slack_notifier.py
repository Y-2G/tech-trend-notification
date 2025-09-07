import logging
from typing import List, Dict, Any
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models.article import Article
from config.settings import settings
from config.profile import profile_manager
from config.messages import get_message, get_nested_message

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
            fallback_text = f"{get_message('weekly_trends_title')} - {len(top_articles)}{get_message('articles_collected')}"
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=fallback_text
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
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": get_message("weekly_trends_title")
            }
        })
        
        # Collection summary if available
        if collection_summary:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{get_message('weekly_overview')}*\n{collection_summary}"
                }
            })
            blocks.append({"type": "divider"})
        
        # Articles summary
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📊 *{len(articles)}{get_message('articles_collected')}*"
            }
        })
        
        # Top articles
        if articles:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔥 {get_message('top_articles')}*"
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
                        "text": f"_{get_message('showing_top_of', shown=10, total=len(articles))}_"
                    }
                ]
            })
        
        # Add timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_{get_message('generated_on', datetime=current_time)}_"
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
            score_label = self._get_score_label(article.score)
            title_text += f" {score_label} _{article.score:.2f}_"
        
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
            details.append(f"📰 {get_message('source')}: {article.source}")
        
        if article.published_date:
            # Format date based on language
            if settings.language == "ja":
                date_str = article.published_date.strftime("%m月%d日")
            else:
                date_str = article.published_date.strftime("%b %d")
            details.append(f"📅 {get_message('published')}: {date_str}")
        
        if article.tags:
            tags_str = " ".join([f"`{tag}`" for tag in article.tags[:3]])
            details.append(f"🏷️ {get_message('tags')}: {tags_str}")
        
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
    
    def _get_score_label(self, score: float) -> str:
        """Get localized score label with emoji."""
        if score >= 0.8:
            return get_nested_message("score_labels", "high")
        elif score >= 0.6:
            return get_nested_message("score_labels", "medium")
        elif score >= 0.4:
            return get_nested_message("score_labels", "low")
        else:
            return get_nested_message("score_labels", "default")
    
    async def send_error_notification(self, error_message: str) -> bool:
        """Send error notification to Slack."""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"⚠️ {get_message('error_title')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{get_message('error_occurred')}*\n```{error_message}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_{get_message('time')} {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}_"
                        }
                    ]
                }
            ]
            
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=get_message("collection_error")
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
            
            logger.info(f"Slack auth successful. Bot user: {auth_response.get('user', 'unknown')}")
            
            # Test channel access - try different approaches
            try:
                # First try with channel name as-is
                channel_info = self.client.conversations_info(channel=self.channel)
                if channel_info["ok"]:
                    logger.info(f"Successfully accessed channel: {channel_info['channel']['name']}")
                    return True
            except SlackApiError as e:
                if e.response['error'] == 'channel_not_found':
                    # Try with # prefix
                    try:
                        channel_with_hash = f"#{self.channel}" if not self.channel.startswith('#') else self.channel
                        channel_info = self.client.conversations_info(channel=channel_with_hash)
                        if channel_info["ok"]:
                            logger.info(f"Successfully accessed channel with #: {channel_info['channel']['name']}")
                            return True
                    except SlackApiError:
                        pass
                    
                    # List available channels for debugging
                    try:
                        channels_response = self.client.conversations_list(types="public_channel,private_channel")
                        if channels_response["ok"]:
                            channel_names = [ch['name'] for ch in channels_response['channels']]
                            logger.error(f"Channel '{self.channel}' not found. Available channels: {channel_names[:10]}")
                        else:
                            logger.error(f"Cannot access Slack channel '{self.channel}' and failed to list channels")
                    except Exception as list_error:
                        logger.error(f"Cannot access channel '{self.channel}' and failed to list channels: {list_error}")
                
                logger.error(f"Slack channel access failed: {e.response['error']}")
                return False
            
        except SlackApiError as e:
            logger.error(f"Slack connection test failed: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Slack connection test error: {e}")
            return False