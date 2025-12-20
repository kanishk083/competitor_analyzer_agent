# Competitor Analyzer Agent

A powerful AI-powered competitor monitoring system that tracks changes on competitor websites and provides intelligent analysis using LLM.

## 🎯 Features

- **Real-time Monitoring**: Uses changedetection.io for webhook-based change detection
- **Differential Analysis**: SHA-256 hash comparison to minimize LLM API costs
- **LLM-Powered Analysis**: Classifies changes (Pricing/Feature/Marketing) using GROQ Llama 3.3
- **Smart Alerts**: Console and Slack notifications with impact scoring
- **SWOT Analysis**: Generate strategic SWOT analysis from monitoring data
- **CSS Selector Targeting**: Focus on specific page elements for precise monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Docker Environment                                          │
│  ┌─────────────────────┐     ┌────────────────────────────┐ │
│  │ changedetection.io  │────▶│ browserless/chrome         │ │
│  │ :5000               │     │ (Playwright) :3000         │ │
│  └─────────┬───────────┘     └────────────────────────────┘ │
└────────────┼────────────────────────────────────────────────┘
             │ Webhook
             ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Application (:8000)                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ Webhook     │─▶│ Differential │─▶│ GROQ LLM Analysis  │  │
│  │ Listener    │  │ Analysis     │  │ (Llama 3.3)        │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│                          │                    │              │
│                   ┌──────▼──────┐      ┌──────▼──────┐      │
│                   │ SQLite DB   │      │ Alerts      │      │
│                   │ (Hashes)    │      │ (Slack/CLI) │      │
│                   └─────────────┘      └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` with your API keys:

```env
GROQ_API_KEY="your-groq-api-key"
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."  # Optional
```

### 3. Start Services (Standalone Mode)

Since Docker is not available, you can run the agent in **Standalone Mode**.
This uses a local Python scheduler instead of changedetection.io webhooks.

```bash
# Start the scheduled monitor
python scheduler.py
```

This will check all competitors defined in `config/competitors.json` every 60 minutes.

### 3b. Start Services (Docker Mode - Optional)

If you have Docker installed:

```bash
docker compose up -d
python main.py
```

```bash
python main.py
# or
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Configure changedetection.io

1. Open http://localhost:5000
2. Add a watch for your competitor URL
3. Go to Settings → Notifications
4. Add webhook: `http://host.docker.internal:8000/webhook/change`

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook/change` | Receive changedetection.io webhooks |
| POST | `/check` | Manually check a URL |
| GET | `/history/{url}` | Get change history for URL |
| GET | `/monitored` | List all monitored URLs |
| GET | `/health` | Health check |

### Example: Manual Check

```bash
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"url": "https://competitor.com/pricing", "selectors": ["#pricing-table"]}'
```

### Example: Webhook Test

```bash
curl -X POST http://localhost:8000/webhook/change \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://competitor.com/pricing",
    "current_snapshot": "New pricing announced: Enterprise plan now $199/month"
  }'
```

## 📊 Change Classification

The LLM analyzes each change and provides:

- **Change Type**: `Pricing`, `Feature`, or `Marketing`
- **Impact Score**: 1-10 (determines if alert is sent)
- **Summary**: What changed and why it matters
- **Counter-Strategy**: Actionable recommendation for Sales team

## 🔧 Scheduled Monitoring

Alternative to webhooks - run periodic checks:

```bash
python scheduler.py
```

Configure competitors in `config/competitors.json`:

```json
{
  "competitors": [
    {
      "name": "Competitor A",
      "url": "https://competitor.com/pricing",
      "selectors": ["#pricing-table", ".pricing-card"],
      "check_interval_minutes": 60,
      "enabled": true
    }
  ]
}
```

## 📁 Project Structure

```
competitor_analyzer_agent/
├── app.py                 # FastAPI webhook listener
├── main.py                # Entry point
├── scheduler.py           # Scheduled monitoring
├── docker-compose.yml     # Docker services
├── requirements.txt       # Dependencies
├── .env                   # Environment variables
├── config/
│   ├── settings.py        # Configuration management
│   └── competitors.json   # Competitor URL config
├── agents/
│   ├── scraper_agent.py   # BeautifulSoup scraper
│   ├── analyzer_agent.py  # GROQ LLM integration
│   ├── extractor_agent.py # Data extraction
│   ├── reporter_agent.py  # Report generation
│   ├── swot_agent.py      # SWOT analysis
│   └── pipeline.py        # Orchestration
├── tools/
│   ├── web_scraper_tool.py    # Standalone scraper
│   └── firecrawl_tool.py      # Firecrawl API
└── utils/
    ├── storage.py         # SQLite hash storage
    └── alerting.py        # Console/Slack alerts
```

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | GROQ API key for Llama 3.3 |
| `GROQ_MODEL` | No | Model name (default: llama-3.3-70b-versatile) |
| `SLACK_WEBHOOK_URL` | No | Slack webhook for alerts |
| `DATABASE_PATH` | No | SQLite database path |
| `WEBHOOK_SECRET` | No | Secret for webhook validation |

## 📝 License

MIT License
