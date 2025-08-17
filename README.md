# Tech Trend Notifier

An automated system that collects, curates, and delivers weekly technology trends and articles directly to your Slack channel. Built with Python and powered by AI for intelligent content summarization and relevance scoring.

## 🚀 Features

- **Multi-Source Collection**: Aggregates content from web search (Tavily), RSS feeds, and social media
- **AI-Powered Processing**: Uses OpenAI GPT-4o-mini for query generation and content summarization
- **Smart Deduplication**: Removes duplicate articles using URL normalization and content similarity
- **Relevance Scoring**: Scores articles based on user interests and content quality
- **Rich Slack Notifications**: Sends formatted summaries using Slack Block Kit
- **Serverless Architecture**: Runs automatically via GitHub Actions with no infrastructure management
- **Configurable Profiles**: Customize interests, keywords, and notification preferences

## 📋 Prerequisites

- Python 3.11+
- GitHub repository with Actions enabled
- API keys for:
  - OpenAI (GPT-4o-mini)
  - Tavily (web search)
  - Slack Bot Token
- Slack workspace with bot permissions

## 🛠️ Setup

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd tech-trend-notifier
cp .env.example .env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_CHANNEL=#your-channel-name
```

### 4. Customize User Profile

Edit `config/profile.yaml` to match your interests:

```yaml
user_profile:
  interests:
    - "Python"
    - "JavaScript"
    - "Machine Learning"
    # Add your tech interests

  keywords:
    high_priority:
      - "breakthrough"
      - "new release"
      # Add priority keywords
```

### 5. Set Up GitHub Secrets

In your GitHub repository, add these secrets:

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL`

## 🎯 Usage

### Automatic Weekly Collection

The system runs automatically every Monday at 09:00 JST via GitHub Actions.

### Manual Execution

```bash
# Full collection
python src/main.py

# Test run (limited scope)
python src/main.py --test

# Health check
python src/main.py --health
```

### Manual GitHub Actions Trigger

1. Go to your repository's Actions tab
2. Select "Weekly Tech Trends Collection"
3. Click "Run workflow"
4. Choose test mode if desired

## 📊 How It Works

1. **Query Generation**: AI generates search queries based on your interests
2. **Content Collection**: Gathers articles from multiple sources in parallel
3. **Deduplication**: Removes duplicates using URL and content similarity
4. **Scoring & Ranking**: Scores articles for relevance and quality
5. **Summarization**: AI generates concise summaries of top articles
6. **Notification**: Sends formatted summary to Slack

## 🔧 Configuration

### User Profile (`config/profile.yaml`)

- **interests**: Your technology interests for content filtering
- **keywords**: High/medium priority and excluded keywords
- **sources**: Enable/disable specific data sources
- **notification**: Slack notification preferences

### Environment Settings (`.env`)

- **API Keys**: Required for external services
- **Rate Limits**: Control API request frequency
- **Content Limits**: Maximum articles per source
- **Similarity Threshold**: Deduplication sensitivity

## 📁 Project Structure

```
tech-trend-notifier/
├── src/
│   ├── collectors/          # Data collection modules
│   ├── processors/          # Content processing pipeline
│   ├── notifiers/          # Notification delivery
│   ├── models/             # Data models
│   ├── config/             # Configuration management
│   └── main.py             # Application entry point
├── config/
│   └── profile.yaml        # User preferences
├── .github/workflows/      # GitHub Actions
└── requirements.txt        # Python dependencies
```

## 🔍 Monitoring

### Logs

- Application logs are written to `tech_trends.log`
- GitHub Actions logs available in the Actions tab
- Failed runs upload logs as artifacts

### Health Checks

```bash
python src/main.py --health
```

Checks connectivity to:

- Slack API
- OpenAI API
- Tavily API
- RSS feeds

## 🚨 Troubleshooting

### Common Issues

1. **API Rate Limits**: Reduce `MAX_ARTICLES_PER_SOURCE` in environment
2. **Slack Permissions**: Ensure bot has `chat:write` and `channels:read` scopes
3. **No Articles Collected**: Check API keys and network connectivity
4. **GitHub Actions Failing**: Verify all secrets are set correctly

### Debug Mode

```bash
LOG_LEVEL=DEBUG python src/main.py --test
```

## 💰 Cost Optimization

- Uses GPT-4o-mini for cost efficiency
- Limits API calls with rate limiting and batching
- Configurable content limits to control usage
- Designed to run within free API tiers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini API
- Tavily for web search capabilities
- Slack for Block Kit and API
- GitHub Actions for serverless execution
