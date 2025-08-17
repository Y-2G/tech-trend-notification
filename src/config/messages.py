"""
Multi-language message definitions for the Tech Trend Notifier
"""

from typing import Dict, Any
from config.settings import settings

# Message definitions by language
MESSAGES = {
    "ja": {
        "weekly_trends_title": "週間技術トレンド",
        "weekly_overview": "今週の概要:",
        "articles_collected": "記事を収集しました",
        "top_articles": "注目記事:",
        "showing_top_of": "全{total}記事中、上位{shown}記事を表示しています。",
        "generated_on": "生成日時: {datetime}",
        "error_title": "技術トレンド収集エラー",
        "error_occurred": "週間収集中にエラーが発生しました:",
        "time": "時刻:",
        "source": "情報源",
        "published": "公開日",
        "tags": "タグ",
        "no_articles": "今週は記事が収集されませんでした。",
        "collection_error": "技術トレンド収集エラー",
        "score_labels": {
            "high": "🔥 高評価",
            "medium": "⭐ 中評価", 
            "low": "👍 低評価",
            "default": "📄"
        }
    },
    "en": {
        "weekly_trends_title": "Weekly Tech Trends",
        "weekly_overview": "This Week's Overview:",
        "articles_collected": "articles collected",
        "top_articles": "Top Articles:",
        "showing_top_of": "Showing top {shown} of {total} articles.",
        "generated_on": "Generated on {datetime}",
        "error_title": "Tech Trends Collection Error",
        "error_occurred": "Error occurred during weekly collection:",
        "time": "Time:",
        "source": "Source",
        "published": "Published",
        "tags": "Tags",
        "no_articles": "No articles were collected this week.",
        "collection_error": "Tech Trends Collection Error",
        "score_labels": {
            "high": "🔥 High",
            "medium": "⭐ Medium",
            "low": "👍 Low", 
            "default": "📄"
        }
    }
}

def get_message(key: str, **kwargs) -> str:
    """Get localized message by key with optional formatting."""
    lang = settings.language
    if lang not in MESSAGES:
        lang = "en"  # fallback to English
    
    message = MESSAGES[lang].get(key, MESSAGES["en"].get(key, key))
    
    if kwargs:
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            return message
    
    return message

def get_nested_message(key: str, subkey: str) -> str:
    """Get nested message (e.g., score_labels.high)."""
    lang = settings.language
    if lang not in MESSAGES:
        lang = "en"
    
    nested = MESSAGES[lang].get(key, MESSAGES["en"].get(key, {}))
    return nested.get(subkey, subkey)