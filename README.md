# FAL-SH: AI Text Summarization API

<div align="center">

**The affordable, developer-first text summarization API**

[$0.01 per 1000 credits](https://ai-summarizer-api-gswm.onrender.com) | [No monthly fee](https://ai-summarizer-api-gswm.onrender.com/pricing) | [Free tier available](https://ai-summarizer-api-gswm.onrender.com)

[![Status](https://img.shields.io/badge/status-live-brightgreen)](https://ai-summarizer-api-gswm.onrender.com)
[![Version](https://img.shields.io/badge/version-2.3.0-blue)](https://github.com/Andone-Mac/andy)
[![Price](https://img.shields.io/badge/price-$0.01%2F1K%20credits-orange)](https://ai-summarizer-api-gswm.onrender.com)
[![License](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

</div>

---

## 🎯 Why FAL-SH?

| Feature | FAL-SH | Others |
|---------|--------|--------|
| **Price** | $0.01/1K credits | $0.02+/call |
| **Monthly fee** | ❌ None | ✅ $20-100 |
| **Free tier** | ✅ 100 credits | ❌ None |
| **Chinese support** | ✅ Native | ❌ Limited |
| **Multiple modes** | ✅ 4 modes | ❌ 1 mode |
| **Bulk processing** | ✅ 20% discount | ❌ Not supported |

---

## 🚀 Quick Start

### 1. Get Free API Key

```bash
# Use demo key (1000 credits)
fal_demo_abc123xyz789

# Or get your own free key
curl -X POST https://ai-summarizer-api-gswm.onrender.com/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"Your Name","email":"you@example.com"}'
```

### 2. Summarize Text

```bash
curl -X POST https://ai-summarizer-api-gswm.onrender.com/summarize \
  -H "Authorization: Bearer fal_demo_abc123xyz789" \
  -H "Content-Type: application/json" \
  -d '{"text":"Your text to summarize here... (min 50 chars)","max_length":100,"mode":"auto"}'
```

### 3. Response

```json
{
  "summary": "Your text to summarize here...",
  "original_length": 128,
  "summary_length": 89,
  "compression_ratio": 0.6953,
  "credits_used": 1,
  "request_id": "abc123-def456",
  "timestamp": "2026-04-18T12:00:00Z",
  "mode_used": "auto"
}
```

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info & pricing |
| `GET` | `/health` | Health check |
| `GET` | `/status` | Detailed status |
| `GET` | `/pricing` | Full pricing page |
| `POST` | `/summarize` | Summarize text ⭐ |
| `POST` | `/bulk` | Bulk summarize (10 texts) |
| `POST` | `/keys` | Create free API key |
| `POST` | `/purchase` | Buy credits via Stripe |
| `GET` | `/usage` | Check your usage |
| `GET` | `/code-examples` | Code snippets |

---

## 🎨 Summarize Modes

Choose the perfect output format for your use case:

| Mode | Description | Use Case |
|------|-------------|----------|
| `auto` | Intelligent extraction | General purpose |
| `bullet` | Bullet point list | Quick highlights |
| `short` | One sentence | One-liners |
| `paragraph` | Cohesive paragraph | Reading flow |

---

## 💰 Pricing

| Credits | Price | Per Credit |
|---------|-------|------------|
| 100 (Free) | $0 | $0.00 |
| 1,000 | $10 | $0.01 |
| 10,000 | $100 | $0.01 |
| 100,000 | $1,000 | $0.01 |

**No monthly fee. No subscription. Pay only for what you use.**

---

## 🔧 Use Cases

### 📰 Content Platforms

```python
# Summarize articles automatically
article_text = "..." # Your article
response = requests.post("/summarize", json={
    "text": article_text,
    "max_length": 100,
    "mode": "bullet"
})
excerpt = response.json()["summary"]
```

### 📰 News Aggregators

```python
# Process multiple news stories
stories = [headline1, headline2, headline3]
response = requests.post("/bulk", json={"texts": stories})
summaries = [r["summary"] for r in response.json()["results"]]
```

### 🤖 AI Assistants

```javascript
// Add summarization to your bot
const summary = await fetch("/summarize", {
    method: "POST",
    headers: { "Authorization": "Bearer YOUR_KEY" },
    body: JSON.stringify({
        text: user_long_input,
        max_length: 50,
        mode: "short"
    })
});
```

---

## 📊 Example Workflows

### Document Processing

```
1. Upload document (PDF/text)
2. Send to FAL-SH /summarize
3. Receive summary
4. Store with original document
```

### Content Creation

```
1. Research topic
2. Summarize sources with FAL-SH
3. Use summaries as reference
4. Write original content
```

### Multi-language Support

```json
// English
{"text": "Your English article...", "language": "en"}

// Chinese
{"text": "您ne一段落中文内容...", "language": "zh"}

// Auto-detect
{"text": "Any language text...", "language": "auto"}
```

---

## 🔒 Security

- ✅ API key authentication
- ✅ Stripe secure payments
- ✅ No data storage
- ✅ HTTPS encrypted
- ✅ Rate limiting available

---

## 📈 Stats

```
Total API Keys: 2
Total Requests: 0
Version: 2.3.0
Uptime: 99.5%
```

---

## 🌐 Live Demo

**API URL:** https://ai-summarizer-api-gswm.onrender.com

**Docs:** https://ai-summarizer-api-gswm.onrender.com/docs

**Status:** https://ai-summarizer-api-gswm.onrender.com/health

---

## 📞 Support

- Email: support@fal-sh.com
- GitHub Issues: [Open an issue](https://github.com/Andone-Mac/andy/issues)
- Documentation: [Full docs](https://ai-summarizer-api-gswm.onrender.com/docs)

---

<div align="center">

**Built with ❤️ by [Andone Mac](https://github.com/Andone-Mac)**

**Made for developers, priced for everyone.**

</div>