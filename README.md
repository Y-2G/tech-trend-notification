# 🤖 AI Engineering Automation Trend Notifier

AI とエンジニアリング自動化の最新トレンドを自動収集・キュレーションし、Slack に日本語で配信するインテリジェントシステム。Python 製で、AI 駆動のコンテンツ要約と関連性スコアリングを搭載。

An intelligent system that automatically collects, curates, and delivers the latest AI and engineering automation trends to your Slack channel in Japanese. Built with Python and powered by AI for intelligent content summarization and relevance scoring.

## 🚀 主要機能 / Key Features

- **🌐 多元的情報収集**: Web 検索(Tavily)、RSS、Reddit、X(Twitter)から自動収集
- **🧠 AI 駆動処理**: OpenAI GPT-4o-mini によるクエリ生成とコンテンツ要約
- **🎯 AI 自動化特化**: GitHub Copilot、Cursor、MLOps、DevOps 自動化に特化
- **📊 スマート重複除去**: URL 正規化とコンテンツ類似性による重複記事除去
- **⭐ 関連性スコアリング**: ユーザー興味とコンテンツ品質に基づく記事スコアリング
- **💬 日本語 Slack 通知**: Slack Block Kit を使用したリッチな日本語フォーマット通知
- **☁️ サーバーレス**: GitHub Actions による自動実行、インフラ管理不要
- **⚙️ 高度設定**: 興味分野、キーワード、通知設定の詳細カスタマイズ
- **🌍 多言語対応**: 日本語・英語の切り替え可能

## 📋 前提条件 / Prerequisites

- Python 3.11+
- GitHub Actions 有効なリポジトリ / GitHub repository with Actions enabled
- 以下の API キー / API keys for:
  - OpenAI (GPT-4o-mini)
  - Tavily (web search)
  - Slack Bot Token
- 適切な権限を持つ Slack ワークスペース / Slack workspace with bot permissions

### 🔑 必要な Slack Bot Scopes

Slack App の設定で以下の scopes を追加してください：

- `chat:write` - メッセージ送信
- `channels:read` - パブリックチャンネル情報読み取り
- `groups:read` - プライベートチャンネル情報読み取り（必要に応じて）
- `chat:write.public` - 未参加チャンネルへの投稿（推奨）

## 🛠️ セットアップ / Setup

### 1. リポジトリのクローンと設定 / Clone and Configure

```bash
git clone <your-repo-url>
cd tech-trend-notifier
cp .env.example .env
```

### 2. 依存関係のインストール / Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定 / Configure Environment Variables

`.env`ファイルに API キーを設定：

```env
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# Tavily API設定
TAVILY_API_KEY=your_tavily_api_key_here

# Slack設定
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL=proj-slack-notification-test

# アプリケーション設定
LANGUAGE=ja  # 日本語の場合、英語の場合は en
LOG_LEVEL=INFO
MAX_ARTICLES_PER_SOURCE=10
SIMILARITY_THRESHOLD=0.8
```

### 4. ユーザープロファイルのカスタマイズ / Customize User Profile

`config/profile.yaml`を編集して AI 自動化に特化した設定に：

```yaml
user_profile:
  name: "AI Engineering Automation Specialist"
  interests:
    # AI/ML Core Technologies
    - "AI"
    - "Machine Learning"
    - "LLM"
    - "GPT"
    - "Claude"
    - "GitHub Copilot"
    - "Cursor"
    - "DevOps Automation"
    - "MLOps"
    # 他の興味分野を追加

  keywords:
    high_priority:
      - "AI automation"
      - "自動化"
      - "workflow automation"
      - "automated deployment"
      - "zero-touch"
      # 優先キーワードを追加
```

### 5. GitHub Secrets の設定 / Set Up GitHub Secrets

GitHub リポジトリの設定で以下のシークレットを追加：

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL`
- `LANGUAGE` (オプション、デフォルト: ja)

## 🎯 使用方法 / Usage

### 自動週次収集 / Automatic Weekly Collection

システムは毎週月曜日 09:00 JST に GitHub Actions 経由で自動実行されます。

### 手動実行 / Manual Execution

```bash
# フル収集 / Full collection
python3 run.py

# テスト実行（限定スコープ）/ Test run (limited scope)
python3 run.py --test

# ヘルスチェック / Health check
python3 run.py --health
```

### GitHub Actions 手動トリガー / Manual GitHub Actions Trigger

1. リポジトリの Actions タブに移動
2. "Weekly Tech Trends Collection"を選択
3. "Run workflow"をクリック
4. 必要に応じてテストモードを選択

### 🌍 言語設定 / Language Settings

```bash
# 日本語で出力
LANGUAGE=ja

# 英語で出力
LANGUAGE=en
```

## 📊 動作原理 / How It Works

1. **🔍 クエリ生成**: AI がユーザーの興味に基づいて検索クエリを生成
2. **📰 コンテンツ収集**: 複数のソースから並列で記事を収集
3. **🔄 重複除去**: URL とコンテンツ類似性を使用して重複を除去
4. **⭐ スコアリング・ランキング**: 関連性と品質で記事をスコアリング
5. **📝 要約生成**: AI が上位記事の簡潔な要約を生成
6. **💬 通知**: フォーマットされた要約を Slack に送信

### 🎯 AI 自動化特化の収集内容例

- **AI コーディングツール**: GitHub Copilot、Cursor、Devin AI の最新機能
- **MLOps 自動化**: MLflow、Kubeflow、自動化パイプライン
- **DevOps 自動化**: Infrastructure as Code、CI/CD、自動デプロイ
- **セキュリティ自動化**: 脆弱性対応、自動修復
- **コスト最適化**: クラウドリソース自動最適化
- **プロダクション事例**: 大手企業の自動化実装事例

## 🔧 設定 / Configuration

### ユーザープロファイル / User Profile (`config/profile.yaml`)

- **interests**: AI 自動化技術の興味分野（60+項目を事前設定済み）
- **keywords**: 高/中優先度キーワードと除外キーワード
- **sources**: 特定データソースの有効/無効設定
- **notification**: Slack 通知設定

#### 🎯 事前設定済みの専門分野

- **AI/ML**: LLM、RAG、Vector Database、Transformers
- **自動化ツール**: GitHub Copilot、Cursor、Devin AI、SWE-agent
- **MLOps**: MLflow、Kubeflow、DVC、Weights & Biases
- **DevOps**: Terraform、Ansible、GitOps、ArgoCD
- **クラウド**: AWS、GCP、Azure、Kubernetes、Serverless
- **監視**: Prometheus、Grafana、OpenTelemetry

### 環境設定 / Environment Settings (`.env`)

- **API Keys**: 外部サービス用 API キー
- **LANGUAGE**: 出力言語（ja/en）
- **Rate Limits**: API リクエスト頻度制御
- **Content Limits**: ソース毎の最大記事数
- **Similarity Threshold**: 重複除去の感度

## 📁 プロジェクト構造 / Project Structure

```
tech-trend-notifier/
├── src/
│   ├── collectors/          # データ収集モジュール / Data collection modules
│   │   ├── base.py         # ベースコレクタークラス
│   │   ├── web_search.py   # Tavily Web検索
│   │   ├── rss_collector.py # RSS/Atomフィード処理
│   │   └── reddit_collector.py # Reddit API統合
│   ├── processors/          # コンテンツ処理パイプライン / Content processing pipeline
│   │   ├── query_generator.py # AI検索クエリ生成
│   │   ├── deduplicator.py    # 重複除去
│   │   ├── scorer.py          # 関連性スコアリング
│   │   └── summarizer.py      # AI要約生成
│   ├── notifiers/          # 通知配信 / Notification delivery
│   │   └── slack_notifier.py # Slack Block Kit統合
│   ├── models/             # データモデル / Data models
│   │   └── article.py      # 記事データ構造
│   ├── config/             # 設定管理 / Configuration management
│   │   ├── settings.py     # 環境変数・設定
│   │   ├── profile.py      # ユーザープロファイル管理
│   │   └── messages.py     # 多言語メッセージ定義
│   └── main.py             # アプリケーションエントリーポイント
├── config/
│   └── profile.yaml        # ユーザー設定 / User preferences
├── .github/workflows/      # GitHub Actions
│   └── weekly_collect.yml  # 週次実行ワークフロー
├── run.py                  # 実行エントリーポイント
└── requirements.txt        # Python依存関係
```

## 🔍 監視・モニタリング / Monitoring

### ログ / Logs

- アプリケーションログは`tech_trends.log`に出力
- GitHub Actions ログは Actions タブで確認可能
- 失敗時はログをアーティファクトとしてアップロード

### ヘルスチェック / Health Checks

```bash
python3 run.py --health
```

以下への接続性をチェック：

- ✅ Slack API
- ✅ OpenAI API
- ✅ Tavily API
- ✅ RSS feeds

### 📊 Slack 通知例 / Sample Slack Notification

```
📈 週間技術トレンド

今週の概要:
今週はAI自動化ツールの進歩とMLOpsプラットフォームの新機能が注目されました...

📊 25記事を収集しました

🔥 注目記事:
1. GitHub Copilot Workspaceの新機能について 🔥 高評価 0.95
   📰 情報源: GitHub Blog • 📅 公開日: 8月15日 • 🏷️ タグ: AI automation GitHub

2. Cursor AIエディタの最新アップデート ⭐ 中評価 0.78
   📰 情報源: Cursor Blog • 📅 公開日: 8月14日 • 🏷️ タグ: AI Code Generation

生成日時: 2025-08-18 09:00 UTC
```

## 🚨 トラブルシューティング / Troubleshooting

### よくある問題 / Common Issues

1. **API レート制限**: 環境変数の`MAX_ARTICLES_PER_SOURCE`を削減
2. **Slack 権限エラー**: Bot に`chat:write`と`channels:read`スコープがあることを確認
3. **記事が収集されない**: API キーとネットワーク接続を確認
4. **GitHub Actions 失敗**: すべてのシークレットが正しく設定されているか確認
5. **日本語が表示されない**: `LANGUAGE=ja`が設定されているか確認

### デバッグモード / Debug Mode

```bash
LOG_LEVEL=DEBUG python3 run.py --test
```

### 🔧 Slack 設定のトラブルシューティング

#### エラー: `missing_scope`

```bash
# 必要なスコープを追加
chat:write
channels:read
groups:read (プライベートチャンネルの場合)
```

#### エラー: `channel_not_found`

```bash
# チャンネル名の確認（#は不要）
SLACK_CHANNEL=proj-slack-notification-test

# またはチャンネルIDを使用
SLACK_CHANNEL=C1234567890
```

## 💰 コスト最適化 / Cost Optimization

- **GPT-4o-mini 使用**: コスト効率の良いモデルを採用
- **レート制限**: API コール数を制限・バッチ処理で最適化
- **設定可能な制限**: 使用量制御のための設定可能なコンテンツ制限
- **無料枠内設計**: 各 API の無料枠内で動作するよう設計
- **週 1 回実行**: 過度な API 使用を避ける適切な実行頻度

### 📊 推定コスト / Estimated Costs

| サービス           | 月間推定コスト | 備考                       |
| ------------------ | -------------- | -------------------------- |
| OpenAI GPT-4o-mini | $2-5           | クエリ生成・要約処理       |
| Tavily API         | $0-10          | Web 検索（無料枠あり）     |
| GitHub Actions     | $0             | パブリックリポジトリは無料 |
| **合計**           | **$2-15/月**   | 使用量により変動           |

## 🚀 今後の拡張予定 / Future Enhancements

- [ ] **Discord 通知対応**: Slack 以外の通知チャンネル
- [ ] **カスタムフィルター**: より詳細な記事フィルタリング
- [ ] **トレンド分析**: 長期的なトレンド分析とレポート
- [ ] **多言語要約**: 英語記事の日本語要約
- [ ] **Webhook 統合**: 外部システムとの連携
- [ ] **ダッシュボード**: Web UI での設定・監視

## 🤝 コントリビューション / Contributing

1. リポジトリをフォーク / Fork the repository
2. フィーチャーブランチを作成 / Create a feature branch
3. 変更を実装 / Make your changes
4. 必要に応じてテストを追加 / Add tests if applicable
5. プルリクエストを送信 / Submit a pull request

## 📄 ライセンス / License

このプロジェクトは MIT ライセンスの下で公開されています。詳細は LICENSE ファイルをご覧ください。

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 謝辞 / Acknowledgments

- **OpenAI** - GPT-4o-mini API 提供
- **Tavily** - Web 検索機能提供
- **Slack** - Block Kit・API 提供
- **GitHub Actions** - サーバーレス実行環境提供
- **Anthropic** - Claude API（将来対応予定）
- **Hugging Face** - オープンソース AI モデル

---

## 📞 サポート / Support

質問やサポートが必要な場合：

- 🐛 **バグレポート**: GitHub の Issues を使用
- 💡 **機能要望**: GitHub の Issues で`enhancement`ラベル
- 📧 **その他**: リポジトリの Discussions を活用

**Happy Automating! 🤖✨**
