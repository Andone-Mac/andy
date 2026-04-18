# FAL-SH: AI Summarizer API

**The affordable, developer-friendly text summarization API**

![Status](https://img.shields.io/badge/status-live-brightgreen)
![Version](https://img.shields.io/badge/version-2.1.0-blue)
![Price](https://img.shields.io/badge/price-%240.01%2F1K%20credits-orange)

---

## 🎯 What is FAL-SH?

FAL-SH is a text summarization API that helps developers and content creators summarize long articles, documents, and text content quickly and affordably.

**Perfect for:**
- 📰 News aggregators summarizing articles
- 📚 Content platforms creating excerpts
- 📄 Document processing pipelines
- 🤖 AI assistants needing text condensation
- 📝 Writing tools for summaries & highlights

---

## 💰 Pricing

| Amount | Price |
|--------|-------|
| 100 credits | $1.00 |
| 1,000 credits | $10.00 |
| 10,000 credits | $100.00 |

**$0.01 per 1,000 characters summarized**

No monthly fee. Pay only for what you use.

---

## 🚀 Quick Start

### 1. Get Your API Key

Use the demo key to test:
```
fal_demo_abc123xyz789
```

Or create your own at `POST /keys`

### 2. Summarize Text

```bash
curl -X POST https://ai-summarizer-api-gswm.onrender.com/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: fal_demo_abc123xyz789" \
  -d '{
    "text": "Your long article text here. This API will summarize it for you efficiently and affordably. Perfect for developers building content applications.",
    "max_length": 50
  }'
```

### 3. Response Example

```json
{
  "summary": "Your long article text here. This API will summarize it...",
  "original_length": 180,
  "summary_length": 65,
  "compression_ratio": 0.36,
  "credits_used": 1,
  "request_id": "abc123-def456",
  "timestamp": "2026-04-18T12:00:00"
}
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `GET` | `/pricing` | Pricing info |
| `GET` | `/stats` | API statistics |
| `POST` | `/summarize` | Summarize text |
| `POST` | `/bulk` | Bulk summarize |
| `POST` | `/keys` | Create API key |
| `POST` | `/purchase` | Buy credits |
| `POST` | `/webhook/stripe` | Stripe webhooks |

---

## 🔧 Features

### ✅ Simple Integration
REST API with straightforward JSON responses. No complex setup.

### ✅ Affordable Pricing
$0.01 per 1,000 characters - the cheapest in market.

### ✅ Credit System
Pay-as-you-go. No subscriptions. No monthly fees.

### ✅ Stripe Integration
Secure checkout with credit card payment.

### ✅ Bulk Support
Process up to 10 texts at once with `/bulk` endpoint.

### ✅ Multi-language
Supports both English and Chinese text.

---

## 📊 Example Use Cases

### Content Platform
```python
def summarize_article(article_text):
    response = requests.post(
        "https://ai-summarizer-api-gswm.onrender.com/summarize",
        headers={"X-API-Key": "YOUR_KEY"},
        json={"text": article_text, "max_length": 100}
    )
    return response.json()["summary"]
```

### News Aggregator
```python
def process_news_batch(news_list):
    results = requests.post(
        "https://ai-summarizer-api-gswm.onrender.com/bulk",
        headers={"X-API-Key": "YOUR_KEY"},
        json={"texts": news_list}
    )
    return [r["summary"] for r in results["results"]]
```

---

## 🔒 Security

- API key authentication required
- Stripe secure payment processing
- No storage of sensitive text data
- Rate limiting available on request

---

## 📞 Support

- Documentation: https://ai-summarizer-api-gswm.onrender.com/docs
- Issues: Create a GitHub issue
- Email: support@example.com

---

## 🌐 Live Demo

**API URL:** https://ai-summarizer-api-gswm.onrender.com

**Swagger Docs:** https://ai-summarizer-api-gswm.onrender.com/docs

**Demo Key:** `fal_demo_abc123xyz789` (1000 free credits)

---

*FAL-SH: Make text summarization affordable for everyone.*