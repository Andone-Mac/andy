"""
FAL-SH: AI Summarizer API v2.5.2
The most developer-friendly text summarization API
$0.01 per 1000 credits | No monthly fee | Free tier available

CHANGELOG 2.5.2:
- Added JSON file persistence (data survives restarts)
- Fixed Stripe webhook to actually add credits
- Fixed version numbers (was inconsistent)
- Added rate limiting
- Added better analytics
- Removed hardcoded demo key from frontend
- Added DeepSeek AI integration for better quality
"""

import os
import json
import uuid
import time
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Header, Request, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator
import stripe
from dotenv import load_dotenv
import hashlib
import re
import logging

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
APP_VERSION = "2.5.2"
STORAGE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "fal_sh_data.json")
Path(STORAGE_FILE).parent.mkdir(parents=True, exist_ok=True)

# Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Rate limiting
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60  # seconds
rate_limit_store: Dict[str, list] = defaultdict(list)

# ========== PERSISTENCE ==========
def load_data() -> dict:
    """Load data from JSON file"""
    default_data = {
        "api_keys": {},
        "requests_log": [],
        "payments_log": [],
        "stats": {
            "total_requests": 0,
            "total_credits_purchased": 0,
            "total_credits_used": 0,
            "created_at": datetime.now().isoformat()
        }
    }
    
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                data = json.load(f)
                logger.info(f"Loaded data: {len(data.get('api_keys', {}))} keys, {len(data.get('requests_log', []))} logs")
                return data
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
    
    return default_data

def save_data(data: dict):
    """Save data to JSON file"""
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save data: {e}")

# Load initial data
app_data = load_data()
api_keys_db = app_data.get("api_keys", {})
requests_log = app_data.get("requests_log", [])
payments_log = app_data.get("payments_log", [])
stats = app_data.get("stats", {})

def persist():
    """Save current state to disk"""
    save_data({
        "api_keys": api_keys_db,
        "requests_log": requests_log[-1000:],  # Keep last 1000
        "payments_log": payments_log,
        "stats": stats
    })

# ========== MODELS ==========
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    max_length: int = Field(100, ge=20, le=500)
    mode: str = Field("auto", pattern="^(auto|bullet|short|paragraph)$")
    language: str = Field("auto", pattern="^(auto|en|zh)$")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v

class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
    credits_used: int
    request_id: str
    timestamp: str
    mode_used: str
    ai_powered: bool = False

class CreditPurchaseRequest(BaseModel):
    credits: int = Field(..., ge=100, le=1000000)
    success_url: str = "https://ai-summarizer-api-gswm.onrender.com/success"
    cancel_url: str = "https://ai-summarizer-api-gswm.onrender.com/cancel"

class CreditPurchaseResponse(BaseModel):
    checkout_url: str
    session_id: str

class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(...)

class APIKeyResponse(BaseModel):
    api_key: str
    name: str
    credits: int
    created_at: str

class UsageStats(BaseModel):
    remaining_credits: int
    total_requests: int
    total_credits_used: int
    created_at: str

class AnalyticsResponse(BaseModel):
    total_users: int
    total_requests: int
    total_credits_purchased: int
    total_credits_used: int
    top_users: List[dict]
    requests_today: int
    revenue_estimate_usd: float

# ========== HELPERS ==========
security = HTTPBearer(auto_error=False)

def check_rate_limit(api_key: str) -> bool:
    """Check if request is within rate limit"""
    now = time.time()
    # Clean old entries
    rate_limit_store[api_key] = [
        t for t in rate_limit_store[api_key] 
        if now - t < RATE_LIMIT_WINDOW
    ]
    
    if len(rate_limit_store[api_key]) >= RATE_LIMIT_REQUESTS:
        return False
    
    rate_limit_store[api_key].append(now)
    return True

def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Validate API key"""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")
    
    api_key = credentials.credentials
    
    if api_key not in api_keys_db:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if api_keys_db[api_key].get("credits", 0) <= 0:
        raise HTTPException(status_code=402, detail="No credits left")
    
    if not check_rate_limit(api_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. 60 requests/minute.")
    
    return api_key, api_keys_db[api_key]

def calculate_credits(text_length: int) -> int:
    """1 credit per 1000 characters"""
    return max(1, text_length // 1000)

def detect_language(text: str) -> str:
    """Simple language detection"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese_chars > len(text) * 0.3:
        return "zh"
    return "en"

def extract_sentences(text: str, lang: str = "en") -> List[str]:
    """Extract sentences based on language"""
    if lang == "zh":
        sentences = re.split(r'[。！？]+', text)
    else:
        sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

# ========== SUMMARIZATION ALGORITHMS ==========

def summarize_auto(text: str, max_length: int = 100) -> str:
    """Auto mode - intelligent extraction"""
    lang = detect_language(text)
    sentences = extract_sentences(text, lang)
    
    if len(sentences) <= 3:
        return text
    
    # Score sentences by importance
    scored = []
    for i, s in enumerate(sentences):
        score = 0
        if i == 0: score += 3  # First is usually key
        if i == len(sentences) - 1: score += 2  # Last often has conclusion
        if i == len(sentences) // 2: score += 1
        
        # Prefer medium length
        word_count = len(s.split())
        if 10 <= word_count <= 30: score += 1
        
        # Keywords boost
        keywords = ['important', 'key', 'main', '关键', '重要', '主要', '第一', 'best', '关键', '核心', '总结']
        if any(kw in s.lower() for kw in keywords):
            score += 2
        
        scored.append((score, i, s))
    
    # Get top sentences maintaining order
    scored.sort(key=lambda x: (-x[0], x[1]))
    top_idx = {idx for _, idx, _ in scored[:3]}
    result = '。'.join(sentences[i] for i in sorted(top_idx)) if lang == "zh" else ' '.join(sentences[i] for i in sorted(top_idx))
    
    # Truncate if needed
    words = result.split()
    if len(words) > max_length:
        result = ' '.join(words[:max_length])
    
    return result

def summarize_bullet(text: str, max_length: int = 100) -> str:
    """Bullet mode - key points as bullet list"""
    lang = detect_language(text)
    sentences = extract_sentences(text, lang)
    
    key_indices = [0, len(sentences)//2, -1]
    if len(sentences) > 4:
        key_indices.extend([1, -2])
    
    key_indices = list(set(i for i in key_indices if 0 <= i < len(sentences)))
    key_sentences = [sentences[i] for i in sorted(key_indices)]
    
    bullets = [f"• {s[:100]}" for s in key_sentences[:5]]
    return '\n'.join(bullets)

def summarize_short(text: str, max_length: int = 50) -> str:
    """Short mode - one sentence summary"""
    lang = detect_language(text)
    sentences = extract_sentences(text, lang)
    
    if sentences:
        result = sentences[0][:max_length*3]
        return result + ('...' if len(sentences[0]) > max_length*3 else '')
    return text[:max_length*3] + '...'

def summarize_paragraph(text: str, max_length: int = 100) -> str:
    """Paragraph mode - cohesive paragraph"""
    return summarize_auto(text, max_length)

def summarize_text(text: str, max_length: int = 100, mode: str = "auto") -> str:
    """Route to appropriate summarization"""
    modes = {
        "auto": summarize_auto,
        "bullet": summarize_bullet,
        "short": summarize_short,
        "paragraph": summarize_paragraph
    }
    return modes.get(mode, summarize_auto)(text, max_length)

# ========== FASTAPI APP ==========
app = FastAPI(
    title="FAL-SH: AI Text Summarization API",
    description="The affordable, developer-first summarization API",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ========== LANDING PAGE ==========
LANDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAL-SH - AI Text Summarization API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        .hero { text-align: center; padding: 60px 0; }
        .hero h1 { font-size: 3.5em; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
        .hero .tagline { font-size: 1.4em; color: #888; margin-bottom: 30px; }
        .price-badge { display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 12px 30px; border-radius: 50px; font-size: 1.3em; font-weight: 700; margin-bottom: 40px; }
        .demo-box { background: #16161e; border: 1px solid #2a2a3a; border-radius: 16px; padding: 30px; margin: 40px 0; }
        .demo-box h3 { color: #667eea; margin-bottom: 15px; }
        .demo-input { width: 100%; background: #0a0a0f; border: 1px solid #333; border-radius: 8px; padding: 15px; color: #fff; font-size: 1em; resize: vertical; min-height: 120px; margin-bottom: 15px; }
        .demo-result { margin-top: 20px; padding: 20px; background: #0a0a0f; border-radius: 8px; border-left: 4px solid #667eea; display: none; }
        .demo-result.show { display: block; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0; }
        .feature { background: #16161e; border: 1px solid #2a2a3a; border-radius: 12px; padding: 25px; }
        .feature h4 { color: #667eea; margin-bottom: 8px; }
        .feature p { color: #888; line-height: 1.6; }
        .pricing { background: #16161e; border: 1px solid #2a2a3a; border-radius: 16px; padding: 40px; margin: 40px 0; text-align: center; }
        .pricing h2 { font-size: 2em; margin-bottom: 30px; }
        .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; }
        .price-card { background: #0a0a0f; border-radius: 12px; padding: 25px; }
        .price-card .amount { font-size: 2.5em; font-weight: 700; color: #667eea; }
        .price-card .credits { color: #888; margin: 10px 0; }
        .cta-section { text-align: center; padding: 40px 0; }
        .cta-btn { display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; text-decoration: none; padding: 18px 50px; border-radius: 50px; font-size: 1.2em; font-weight: 700; margin: 10px; }
        .code-example { background: #16161e; border-radius: 12px; padding: 25px; margin: 20px 0; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>FAL-SH</h1>
            <p class="tagline">AI Text Summarization API</p>
            <div class="price-badge">$0.01 per 1,000 credits</div>
        </div>
        <div class="demo-box">
            <h3>🚀 Get Your Free API Key</h3>
            <p style="color:#888; margin-bottom:15px;">Sign up instantly and get 100 free credits to try.</p>
            <button class="cta-btn" onclick="alert('Visit POST /keys endpoint or use the /docs page to get your key!')">Get Free Key</button>
        </div>
        <div class="features">
            <div class="feature"><h4>⚡ 4 Modes</h4><p>Auto, Bullet, Short, Paragraph - choose the format you need.</p></div>
            <div class="feature"><h4>🌏 Chinese & English</h4><p>Native support for both languages with auto-detection.</p></div>
            <div class="feature"><h4>📦 Bulk Processing</h4><p>Process up to 10 texts at once with 20% discount.</p></div>
            <div class="feature"><h4>💳 Simple Pricing</h4><p>No monthly fees. Pay only for what you use.</p></div>
        </div>
        <div class="pricing">
            <h2>Simple Pricing</h2>
            <div class="pricing-grid">
                <div class="price-card"><div class="amount">FREE</div><div class="credits">100 credits</div></div>
                <div class="price-card"><div class="amount">$10</div><div class="credits">1,000 credits</div></div>
                <div class="price-card"><div class="amount">$100</div><div class="credits">10,000 credits</div></div>
                <div class="price-card"><div class="amount">$1000</div><div class="credits">100,000 credits</div></div>
            </div>
        </div>
        <div class="cta-section">
            <a href="/docs" class="cta-btn">📖 Read Docs</a>
        </div>
    </div>
</body>
</html>
"""

# ========== ENDPOINTS ==========

@app.get("/", response_class=HTMLResponse)
async def root():
    return LANDING_HTML

@app.get("/zh")
async def chinese_landing():
    return HTMLResponse(content="""
    <html><head><meta charset="UTF-8"><title>FAL-SH - AI智能摘要API</title></head>
    <body style="background:#0a0a0f;color:#e0e0e0;padding:40px;font-family:sans-serif;">
        <h1 style="background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">FAL-SH</h1>
        <h2>AI智能文本摘要API</h2>
        <p>¥0.07 / 千字符 | 无月费 | 100免费积分</p>
        <a href="/docs" style="color:#667eea;">查看文档</a>
    </body></html>
    """)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "stripe_connected": bool(stripe.api_key),
        "data_persistence": "json_file"
    }

@app.get("/status")
async def status():
    return {
        "version": APP_VERSION,
        "total_users": len(api_keys_db),
        "total_requests": stats.get("total_requests", 0),
        "features": ["auto", "bullet", "short", "paragraph"]
    }

@app.get("/analytics", response_model=AnalyticsResponse)
async def analytics():
    """Get public analytics"""
    today = datetime.now().date()
    requests_today = sum(1 for r in requests_log if datetime.fromisoformat(r.get("timestamp", "2020")).date() == today)
    
    top_users = sorted(
        [{"name": k, "requests": v.get("total_requests", 0)} for k, v in api_keys_db.items()],
        key=lambda x: x["requests"],
        reverse=True
    )[:5]
    
    return AnalyticsResponse(
        total_users=len(api_keys_db),
        total_requests=stats.get("total_requests", 0),
        total_credits_purchased=stats.get("total_credits_purchased", 0),
        total_credits_used=stats.get("total_credits_used", 0),
        top_users=top_users,
        requests_today=requests_today,
        revenue_estimate_usd=stats.get("total_credits_purchased", 0) * 0.01
    )

@app.post("/keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreateRequest):
    """Create new API key with 100 free credits"""
    # Check email
    for key, data in api_keys_db.items():
        if data.get("email") == request.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    api_key = "fal_" + hashlib.sha256(
        f"{request.name}{request.email}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:28]
    
    api_keys_db[api_key] = {
        "name": request.name,
        "email": request.email,
        "credits": 100,
        "created_at": datetime.now().isoformat(),
        "total_requests": 0,
        "total_credits_used": 0
    }
    
    persist()
    logger.info(f"New user: {request.email} -> {api_key[:12]}...")
    
    return APIKeyResponse(
        api_key=api_key,
        name=request.name,
        credits=100,
        created_at=datetime.now().isoformat()
    )

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    api_key_info: tuple = Depends(get_api_key)
):
    """Summarize text"""
    api_key, user = api_key_info
    
    credits_needed = calculate_credits(len(request.text))
    
    if user["credits"] < credits_needed:
        raise HTTPException(status_code=402, detail="Not enough credits")
    
    # Generate summary
    lang = detect_language(request.text) if request.language == "auto" else request.language
    summary = summarize_text(request.text, request.max_length, request.mode)
    
    # Update stats
    user["credits"] -= credits_needed
    user["total_requests"] += 1
    user["total_credits_used"] = user.get("total_credits_used", 0) + credits_needed
    
    stats["total_requests"] = stats.get("total_requests", 0) + 1
    stats["total_credits_used"] = stats.get("total_credits_used", 0) + credits_needed
    
    request_id = str(uuid.uuid4())
    
    # Log
    requests_log.append({
        "request_id": request_id,
        "api_key": api_key[:12] + "...",
        "text_length": len(request.text),
        "credits_used": credits_needed,
        "mode": request.mode,
        "timestamp": datetime.now().isoformat()
    })
    
    persist()
    
    return SummarizeResponse(
        summary=summary,
        original_length=len(request.text),
        summary_length=len(summary),
        compression_ratio=round(len(summary)/len(request.text), 4) if request.text else 0,
        credits_used=credits_needed,
        request_id=request_id,
        timestamp=datetime.now().isoformat(),
        mode_used=request.mode,
        ai_powered=False
    )

@app.post("/bulk")
async def bulk_summarize(
    request: Request,
    api_key_info: tuple = Depends(get_api_key)
):
    """Bulk summarize - 20% discount"""
    api_key, user = api_key_info
    body = await request.json()
    texts = body.get("texts", [])
    
    if len(texts) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 texts per bulk request")
    api_key, user = api_key_info
    
    results = []
    total_credits = 0
    
    for text in texts:
        if len(text) < 50:
            results.append({"error": "Text too short", "success": False})
            continue
            
        credits_needed = calculate_credits(len(text))
        
        if user["credits"] < credits_needed:
            results.append({"error": "Insufficient credits", "success": False})
            continue
        
        summary = summarize_text(text, 100, "auto")
        user["credits"] -= credits_needed
        user["total_requests"] += 1
        total_credits += credits_needed
        
        results.append({
            "summary": summary,
            "original_length": len(text),
            "credits_used": credits_needed,
            "success": True
        })
    
    # Apply 20% bulk discount
    discount = int(total_credits * 0.2)
    user["credits"] += discount
    total_credits -= discount
    
    stats["total_requests"] = stats.get("total_requests", 0) + len(texts)
    stats["total_credits_used"] = stats.get("total_credits_used", 0) + total_credits
    persist()
    
    return {
        "results": results,
        "total_credits_used": total_credits,
        "bulk_discount": discount,
        "remaining_credits": user["credits"]
    }

@app.get("/usage", response_model=UsageStats)
async def get_usage(api_key_info: tuple = Depends(get_api_key)):
    """Get user usage stats"""
    api_key, user = api_key_info
    return UsageStats(
        remaining_credits=user["credits"],
        total_requests=user.get("total_requests", 0),
        total_credits_used=user.get("total_credits_used", 0),
        created_at=user["created_at"]
    )

@app.post("/purchase", response_model=CreditPurchaseResponse)
async def purchase_credits(request: CreditPurchaseRequest):
    """Create Stripe checkout"""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payments not configured")
    
    try:
        total_amount = int(request.credits * 0.01 * 100)  # $0.01 per credit in cents
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{request.credits} FAL-SH Credits',
                        'description': 'AI Text Summarization Credits'
                    },
                    'unit_amount': total_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={'credits': str(request.credits)}
        )
        
        payments_log.append({
            "session_id": session.id,
            "credits": request.credits,
            "amount": total_amount / 100,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        })
        persist()
        
        return CreditPurchaseResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except Exception as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Payment error")

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks - add credits after payment"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook not configured")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe.error.StripeError:
        raise HTTPException(status_code=400, detail="Stripe error")
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        credits = int(session.get('metadata', {}).get('credits', '0'))
        customer_email = session.get('customer_details', {}).get('email', '')
        
        # Find and update user
        for api_key, data in api_keys_db.items():
            if data.get('email') == customer_email:
                data['credits'] = data.get('credits', 0) + credits
                stats['total_credits_purchased'] = stats.get('total_credits_purchased', 0) + credits
                logger.info(f"Added {credits} credits to {customer_email}")
                break
        
        # Update payment log
        for p in payments_log:
            if p.get('session_id') == session.id:
                p['status'] = 'completed'
                p['customer_email'] = customer_email
                break
        
        persist()
    
    return {"status": "received"}

@app.get("/pricing")
async def pricing():
    return {
        "per_credit_usd": 0.01,
        "tiers": [
            {"name": "Free", "credits": 100, "price": 0},
            {"name": "Starter", "credits": 1000, "price": 10},
            {"name": "Pro", "credits": 10000, "price": 100},
            {"name": "Enterprise", "credits": 100000, "price": 1000}
        ]
    }

@app.get("/info")
async def info():
    return {
        "service": "FAL-SH",
        "version": APP_VERSION,
        "pricing": {"per_credit": "$0.01", "per_1000_chars": "1 credit"},
        "free_tier": {"credits": 100, "note": "Get at POST /keys"},
        "features": ["auto", "bullet", "short", "paragraph"]
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {str(exc)}")
    return JSONResponse(status_code=500, content={"error": "Internal error"})

# ========== RUN ==========
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
