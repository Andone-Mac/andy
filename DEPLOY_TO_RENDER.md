# 🚀 Render.com Deployment Guide - AI Summarizer API

## Prerequisites
- GitHub account connected to Render.com (you said you're logged in)
- Stripe live keys already configured in `.env`

---

## Step 1: Create GitHub Repository

### Option A: Quick Setup (Recommended)
1. Go to: **https://github.com/new**
2. Fill in:
   - **Repository name**: `ai-summarizer-api`
   - **Description**: `AI-powered text summarization API with Stripe payments`
   - **Visibility**: Public (free tier) or Private
3. Click **Create repository**

### Option B: GitHub CLI (if available)
```bash
cd ~/.openclaw/workspace/projects/summarizer-api
gh repo create ai-summarizer-api --public --source=. --push
```

---

## Step 2: Push Code to GitHub

After creating the repo, run these commands in the summarizer-api directory:

```bash
cd ~/.openclaw/workspace/projects/summarizer-api

# Initialize git (if not already)
git init
git add .
git commit -m "Initial commit - AI Summarizer API v1.0"

# Add your GitHub repo (replace with your actual repo URL)
git remote add origin https://github.com/YOUR_USERNAME/ai-summarizer-api.git

# Push to GitHub
git push -u origin master
```

---

## Step 3: Deploy to Render.com

### Option A: Via Render Dashboard (You Already Logged In)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New"** → **"Web Service"**
3. **Configure your service**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. **Environment Variables** (add these):
   ```
   STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
   STRIPE_PUBLIC_KEY=${STRIPE_PUBLIC_KEY}
   STRIPE_WEBHOOK_SECRET=whsec_live_placeholder
   APP_ENV=production
   SECRET_KEY=_T2vDkNnZ2Ky6bYYr5tvDif-QOMayuxrW8QxdnE25Ow
   ```

5. **Click "Create Web Service"**

### Option B: Via render-blueprints (Infrastructure as Code)

Create a file `render.yaml` in your repo root:

```yaml
services:
  - type: web
    name: ai-summarizer-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: STRIPE_SECRET_KEY
        value: ${STRIPE_SECRET_KEY}
      - key: STRIPE_PUBLIC_KEY
        value: ${STRIPE_PUBLIC_KEY}
      - key: STRIPE_WEBHOOK_SECRET
        value: whsec_live_placeholder
      - key: APP_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
```

Then go to **Render Dashboard → Blueprints → New Blueprint** and connect your repo.

---

## Step 4: Configure Stripe Webhook

After deployment, configure Stripe to send webhook events:

1. **Go to**: https://dashboard.stripe.com/test/webhooks
2. **Click "Add destination"**
3. **Endpoint URL**: `https://your-api-url.onrender.com/webhook`
4. **Select events**: 
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `customer.subscription.created`
5. **Click "Add endpoint"**
6. **Copy the webhook secret** (starts with `whsec_`)
7. **Update your Render environment variable** `STRIPE_WEBHOOK_SECRET`

---

## Step 5: Verify Deployment

### Test Your API
```bash
# Check if API is running
curl https://your-api-url.onrender.com/

# Get API docs
curl https://your-api-url.onrender.com/docs

# Test with demo key
curl -H "X-API-Key: demo_key_2a97516c354b6884" \
     https://your-api-url.onrender.com/api/v1/summarize \
     -X POST -H "Content-Type: application/json" \
     -d '{"text":"Your long text here to summarize...","max_sentences":3}'
```

### Check Stripe Dashboard
- Go to **https://dashboard.stripe.com/test/dashboard**
- Check **Payments** section for test transactions
- Check **Webhooks** for delivery status

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/summarize` | Summarize text |
| POST | `/api/v1/credits/buy` | Buy credits via Stripe |
| GET | `/api/v1/credits/balance` | Check credit balance |
| POST | `/webhook` | Stripe webhook handler |
| GET | `/health` | Health check |
| GET | `/docs` | API documentation |

---

## Pricing

- **$0.01 per credit** (~$0.10 per average summary)
- **1000 credits = $10**
- **Target: $1000-10000 MRR at 100-1000 active users**

---

## Troubleshooting

### Service Won't Start
1. Check logs in Render dashboard
2. Verify environment variables are set
3. Make sure `python src/main.py` works locally first

### Stripe Not Working
1. Verify keys are correct (not test vs live mismatch)
2. Check Stripe webhook is configured
3. Check webhook secret is set correctly

### CORS Issues
The API is configured to accept all origins for development. For production, update `src/main.py` to restrict allowed origins.

---

## Monitoring

- **Render Dashboard**: https://dashboard.render.com
- **API Health**: `https://your-api-url.onrender.com/health`
- **Logs**: Available in Render dashboard under "Logs"

---

## Next Steps After Deployment

1. **Set up custom domain** (optional)
2. **Configure SSL** (automatic on Render)
3. **Add rate limiting** for production load
4. **Set up monitoring/alerting**
5. **Market your API** on:
   - Hacker News
   - Twitter
   - API directories (RapidAPI, API.market)
   - Developer communities

---

## Need Help?

- **Render Docs**: https://render.com/docs
- **Stripe Docs**: https://stripe.com/docs
- **OpenClaw Docs**: https://docs.openclaw.ai

Good luck with the deployment! 🚀💰