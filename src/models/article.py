from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class Article(BaseModel):
    """Article data model with validation."""
    
    title: str = Field(..., min_length=1, max_length=500)
    url: HttpUrl
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    source: str = Field(..., min_length=1)
    source_type: str = Field(..., regex="^(web_search|rss|twitter|reddit)$")
    tags: List[str] = Field(default_factory=list)
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = Field(default=False)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: str
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.dict()
    
    def __hash__(self) -> int:
        """Hash based on URL for deduplication."""
        return hash(str(self.url))
    
    def __eq__(self, other) -> bool:
        """Equality based on URL."""
        if not isinstance(other, Article):
            return False
        return str(self.url) == str(other.url)


class ProcessedArticleCollection(BaseModel):
    """Collection of processed articles with metadata."""
    
    articles: List[Article]
    total_collected: int
    total_processed: int
    collection_date: datetime = Field(default_factory=datetime.utcnow)
    sources_used: List[str]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }