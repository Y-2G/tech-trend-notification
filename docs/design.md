要件を踏まえて、実装設計を以下のように提案します。

## 1. システムアーキテクチャ

### 実行環境の選択

**GitHub Actions + サーバーレス構成**を推奨します。

```
┌─────────────────────────────────────────────┐
│  GitHub Actions (スケジューラー)              │
│  - 週次実行（cron: "0 0 * * MON"）           │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  メイン処理 (Python Script)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │プロファイル│→│収集エンジン│→│配信エンジン│ │
│  │  マネージャ│  │          │  │          │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
             │                    │
             ▼                    ▼
    ┌────────────────┐    ┌────────────────┐
    │ 外部API群      │    │ Slack API     │
    │ - Web Search  │    └────────────────┘
    │ - X API       │
    │ - Reddit API  │
    └────────────────┘
```

### 選定理由

- **コスト効率**: GitHub Actions の無料枠で運用可能
- **管理簡易性**: インフラ管理不要
- **信頼性**: GitHub の高可用性を活用

## 2. 技術スタック

```yaml
言語・フレームワーク:
  - Python 3.11+
  - asyncio (非同期処理)

AI/LLM:
  - OpenAI API (GPT-4o-mini) # クエリ生成・要約用

情報収集:
  - Tavily API # Web検索（技術記事特化）
  - feedparser # RSS/Atom
  - tweepy # X API v2
  - asyncpraw # Reddit API

処理ライブラリ:
  - aiohttp # 非同期HTTP
  - beautifulsoup4 # HTML解析
  - scikit-learn # テキスト類似度計算
  - pydantic # データ検証

通知:
  - slack-sdk # Slack Block Kit対応

設定管理:
  - python-dotenv # 環境変数
  - PyYAML # 設定ファイル
```

## 3. コンポーネント設計

### 3.1 ディレクトリ構造

```
tech-trend-notifier/
├── .github/
│   └── workflows/
│       └── weekly_collect.yml    # GitHub Actions定義
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── profile.py           # プロファイル管理
│   │   └── settings.py          # 環境変数・設定
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py             # 収集基底クラス
│   │   ├── web_search.py       # Web検索
│   │   ├── rss_collector.py    # RSS/Atom
│   │   ├── x_collector.py      # X API
│   │   └── reddit_collector.py # Reddit API
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── query_generator.py  # AIクエリ生成
│   │   ├── deduplicator.py    # 重複除去
│   │   ├── scorer.py          # スコアリング
│   │   └── summarizer.py      # AI要約
│   ├── notifiers/
│   │   ├── __init__.py
│   │   └── slack_notifier.py  # Slack配信
│   ├── models/
│   │   ├── __init__.py
│   │   └── article.py         # データモデル
│   └── main.py                 # エントリーポイント
├── config/
│   └── profile.yaml            # ユーザープロファイル
├── requirements.txt
├── .env.example
└── README.md
```

### 3.2 主要クラス設計## 4. API 選定と設定

### 4.1 外部 API 選定理由

| API                    | 選定理由                                 | 料金            | 制限                 |
| ---------------------- | ---------------------------------------- | --------------- | -------------------- |
| **Tavily API**         | 技術記事特化の検索 API、開発者向け最適化 | 1000 回/月 無料 | 週 4 回なら十分      |
| **OpenAI GPT-4o-mini** | コスト効率が良く、要約品質も十分         | $0.15/1M 入力   | 週次なら$1 以下      |
| **X API v2 Basic**     | 技術系の速報性が高い                     | $100/月         | Tweet 読取 1 万件/月 |
| **Reddit API**         | 技術議論が活発、無料枠あり               | 無料            | 60req/分             |

### 4.2 設定ファイル例

```yaml
# config/profile.yaml
profile:
  categories:
    - "Web開発"
    - "AI/機械学習"
    - "DevOps"

  keywords:
    required:
      - "Next.js"
      - "TypeScript"
    optional:
      - "performance"
      - "新機能"
      - "ベストプラクティス"
    exclude:
      - "初心者"
      - "入門"

  sources:
    rss_feeds:
      - https://zenn.dev/feed
      - https://dev.to/feed
      - https://web.dev/feed.xml
    reddit_subreddits:
      - "nextjs"
      - "typescript"
      - "webdev"

  notification:
    max_articles: 10
    summary_length: 150
    language: "ja"
```

## 5. エラーハンドリング戦略

```python
# エラー処理とリトライ設計

class ErrorHandler:
    """統一エラーハンドリング"""

    @staticmethod
    def with_retry(max_attempts=3, delay=1):
        """リトライデコレーター"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except (RateLimitError, TemporaryError) as e:
                        last_exception = e
                        wait_time = delay * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                    except PermanentError as e:
                        # 回復不可能なエラーは即座に諦める
                        print(f"Permanent error: {e}")
                        return None

                print(f"Max retries exceeded: {last_exception}")
                return None
            return wrapper
        return decorator

class CircuitBreaker:
    """サーキットブレーカーパターン"""
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

## 6. GitHub Actions 設定

```yaml
# .github/workflows/weekly_collect.yml
name: Weekly Tech Trend Collection

on:
  schedule:
    # 毎週月曜日 09:00 JST (00:00 UTC)
    - cron: "0 0 * * MON"
  workflow_dispatch: # 手動実行も可能

jobs:
  collect-and-notify:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run collection
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
          X_BEARER_TOKEN: ${{ secrets.X_BEARER_TOKEN }}
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL: ${{ secrets.SLACK_CHANNEL }}
        run: |
          python src/main.py

      - name: Notify on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: custom
          custom_payload: |
            {
              text: "❌ 週次Tech Trend収集が失敗しました",
              attachments: [{
                color: 'danger',
                text: `Workflow: ${process.env.AS_WORKFLOW}\nError: Check GitHub Actions logs`
              }]
            }
```

## 7. パフォーマンス最適化

```python
# 非同期並列処理の実装例

class PerformanceOptimizer:
    """パフォーマンス最適化"""

    @staticmethod
    async def fetch_concurrent(urls: List[str], max_concurrent=10):
        """並列フェッチ（セマフォで同時実行数制御）"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(session, url):
            async with semaphore:
                return await fetch_url(session, url)

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_with_semaphore(session, url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def batch_process(items: List, batch_size=10):
        """バッチ処理でメモリ効率化"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
```

## 8. セキュリティ設計

```python
# .env.example
# API Keys (GitHub Secretsで管理)
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
X_BEARER_TOKEN=AAA...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL=#tech-trends

# 設定
MAX_ARTICLES=10
COLLECTION_DAYS_BACK=7
DEBUG_MODE=false
```

## 9. 運用・監視設計

### 監視項目

- **実行成功/失敗**: GitHub Actions 通知
- **収集記事数**: Slack 配信時に表示
- **API 利用量**: 各 API のダッシュボードで確認
- **エラー率**: ログ出力

### 手動実行用 Slack コマンド（オプション）

```python
# Slack Slash Command対応
@app.command("/trend")
async def handle_trend_command(ack, command, respond):
    await ack()

    if command['text'] == 'now':
        # GitHub Actions APIを叩いて手動実行
        trigger_github_action()
        await respond("収集を開始しました。10分程度お待ちください。")
```

## 10. 実装優先順位（MVP）

1. **Phase 1** (1 週目)

   - 基本的な収集機能（Tavily API のみ）
   - シンプルな Slack 通知
   - GitHub Actions 設定

2. **Phase 2** (2 週目)

   - OpenAI 要約機能追加
   - 重複除去実装
   - エラーハンドリング強化

3. **Phase 3** (3 週目)
   - X API、Reddit API 追加
   - スコアリング実装
   - Block Kit 改善

この設計により、メンテナンス性が高く、拡張可能な週次技術トレンド通知システムを構築できます。
