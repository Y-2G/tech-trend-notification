import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field


class SourceConfig(BaseModel):
    """Configuration for individual data sources."""
    enabled: bool = True


class WebSearchConfig(SourceConfig):
    """Web search specific configuration."""
    max_results: int = 15


class RSSConfig(SourceConfig):
    """RSS feed specific configuration."""
    feeds: List[str] = Field(default_factory=list)


class TwitterConfig(SourceConfig):
    """Twitter/X specific configuration."""
    accounts: List[str] = Field(default_factory=list)


class RedditConfig(SourceConfig):
    """Reddit specific configuration."""
    subreddits: List[str] = Field(default_factory=list)


class SourcesConfig(BaseModel):
    """All data sources configuration."""
    web_search: WebSearchConfig = Field(default_factory=WebSearchConfig)
    rss_feeds: RSSConfig = Field(default_factory=RSSConfig)
    x_twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    reddit: RedditConfig = Field(default_factory=RedditConfig)


class KeywordsConfig(BaseModel):
    """Keywords configuration for filtering."""
    high_priority: List[str] = Field(default_factory=list)
    medium_priority: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)


class SlackNotificationConfig(BaseModel):
    """Slack notification configuration."""
    enabled: bool = True
    max_articles: int = 20
    include_summary: bool = True
    include_score: bool = True


class NotificationConfig(BaseModel):
    """Notification configuration."""
    slack: SlackNotificationConfig = Field(default_factory=SlackNotificationConfig)


class UserProfile(BaseModel):
    """User profile configuration model."""
    name: str = "Tech Team"
    interests: List[str] = Field(default_factory=list)
    keywords: KeywordsConfig = Field(default_factory=KeywordsConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)


class ProfileManager:
    """Manages user profile configuration."""
    
    def __init__(self, profile_path: str = "config/profile.yaml"):
        self.profile_path = Path(profile_path)
        self._profile: Optional[UserProfile] = None
    
    def load_profile(self) -> UserProfile:
        """Load user profile from YAML file."""
        if self._profile is not None:
            return self._profile
        
        if not self.profile_path.exists():
            # Create default profile if file doesn't exist
            self._profile = UserProfile()
            self.save_profile(self._profile)
            return self._profile
        
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Extract user_profile section
            profile_data = data.get('user_profile', {})
            self._profile = UserProfile(**profile_data)
            return self._profile
            
        except Exception as e:
            print(f"Error loading profile: {e}")
            # Return default profile on error
            self._profile = UserProfile()
            return self._profile
    
    def save_profile(self, profile: UserProfile) -> None:
        """Save user profile to YAML file."""
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'user_profile': profile.dict()
        }
        
        with open(self.profile_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        
        self._profile = profile
    
    @property
    def profile(self) -> UserProfile:
        """Get current user profile."""
        return self.load_profile()


# Global profile manager instance
profile_manager = ProfileManager()