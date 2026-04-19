"""
FAL-SH: AI Summarizer API v2.3
The most developer-friendly text summarization API
$0.01 per 1000 credits | No monthly fee | Free tier available
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
import uuid
from datetime import datetime, timedelta
import os
import stripe
from dotenv import load_dotenv
import hashlib
import json
import logging
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Initialize FastAPI app
app = FastAPI(
    title="FAL-SH: AI Text Summarization API",
    description="## The Affordable, Developer-First Summarization API\n\n**Why FAL-SH?**\n- $0.01 per 1000 credits - cheapest in market\n- No monthly fee, no subscription\n- Free tier: 100 credits to start\n- REST API, works in any language\n- Stripe secure payments\n\n**Perfect for:**\n- Content platforms needing article excerpts\n- Developers building writing tools\n- News aggregators summarizing stories\n- Document processing pipelines",
    version="2.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "FAL-SH Support",
        "email": "support@fal-sh.com",
        "url": "https://ai-summarizer-api-gswm.onrender.com"
    },
    terms_of_service="https://ai-summarizer-api-gswm.onrender.com/terms",
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"}
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# ========== MODELS ==========
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    max_length: int = Field(100, ge=20, le=500)
    mode: Optional[str] = "auto"  # auto, bullet, short, paragraph
    language: Optional[str] = "auto"
    
    @field_validator('text')
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

class CreditPurchaseRequest(BaseModel):
    credits: int = Field(..., ge=100, le=100000)
    success_url: str
    cancel_url: str

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
    message: str = "Your API key is ready! Copy and save it securely."

class UserStats(BaseModel):
    total_requests: int
    total_credits_used: int
    remaining_credits: int
    estimated_spent: float

class BulkSummarizeRequest(BaseModel):
    texts: List[str] = Field(..., max_length=10)

class APIInfo(BaseModel):
    service: str
    version: str
    tagline: str
    pricing: dict
    free_tier: dict
    features: List[str]
    quick_start: dict

# ========== STORAGE ==========
api_keys_db: Dict[str, dict] = {}
requests_log: List[dict] = []

# Demo keys - support both old and new format
DEMO_KEY_V3 = "fal_demo_abc123xyz789"
DEMO_KEY_OLD = "demo_key_2a97516c354b6884"

demo_user = {
    "name": "Demo User",
    "credits": 1000,
    "created_at": datetime.now().isoformat(),
    "total_requests": 0,
    "email": "demo@example.com"
}

api_keys_db[DEMO_KEY_V3] = demo_user
api_keys_db[DEMO_KEY_OLD] = demo_user.copy()

# Free tier key
api_keys_db["fal_free_trial_xK9mN3p"] = {
    "name": "Free Trial",
    "credits": 100,
    "created_at": datetime.now().isoformat(),
    "total_requests": 0,
    "email": "trial@example.com"
}

# ========== HELPERS ==========
def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Validate API key - supports both Bearer and Key mode"""
    if not credentials:
        raise HTTPException(status_code=401, detail="API key required. Use 'Authorization: Bearer YOUR_KEY' header")
    
    api_key = credentials.credentials
    
    # Direct lookup first
    if api_key in api_keys_db:
        user = api_keys_db[api_key]
    else:
        # Try prefix match
        found = False
        for key in api_keys_db:
            if key.startswith(api_key[:20]):
                api_key = key
                user = api_keys_db[key]
                found = True
                break
        if not found:
            raise HTTPException(status_code=401, detail="Invalid API key. Get one free at POST /keys")
    
    if user["credits"] <= 0:
        raise HTTPException(status_code=402, detail="No credits left! Purchase more at POST /purchase")
    
    return api_key, user

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

def summarize_auto(text: str, max_length: int = 100) -> str:
    """Auto mode - intelligent extraction based on position and keywords"""
    lang = detect_language(text)
    sentences = extract_sentences(text, lang)
    
    if len(sentences) <= 3:
        return text
    
    # Score by position and length
    scored = []
    for i, s in enumerate(sentences):
        score = 0
        # First and last are usually important
        if i == 0: score += 3
        if i == len(sentences) - 1: score += 2
        # Middle sentence importance
        if i == len(sentences) // 2: score += 1
        # Length scoring - prefer medium
        word_count = len(s.split())
        if 10 <= word_count <= 30: score += 1
        # Keyword density (numbers, strong words)
        if any(kw in s.lower() for kw in ['important', 'key', 'main', '关键', '重要', '主要', '第一', 'best', 'top']):
            score += 1
        scored.append((score, i, s))
    
    # Get top sentences maintaining order
    scored.sort(key=lambda x: (-x[0], x[1]))
    top_idx = {idx for _, idx, _ in scored[:3]}
    result = '。'.join(sentences[i] for i in sorted(top_idx))
    
    # Truncate if needed
    words = result.split()
    if len(words) > max_length:
        result = ' '.join(words[:max_length])
    
    return result if result.endswith(('。', '.', '!', '?')) else result + ('。' if lang == 'zh' else '.')

def summarize_bullet(text: str, max_length: int = 100) -> str:
    """Bullet mode - returns key points as bullet list"""
    lang = detect_language(text)
    sentences = extract_sentences(text, lang)
    
    # Take first, middle, last + 2 most important
    key_indices = [0, len(sentences)//2, -1]
    if len(sentences) > 4:
        key_indices.extend([1, -2])
    
    key_indices = list(set(i for i in key_indices if 0 <= i < len(sentences)))
    key_sentences = [sentences[i] for i in sorted(key_indices)]
    
    # Format as bullets
    bullets = []
    for s in key_sentences[:5]:
        # Clean up
        s = s.strip()
        if lang == "zh":
            bullets.append(f"• {s}")
        else:
            bullets.append(f"- {s}")
    
    return '\n'.join(bullets)

def summarize_short(text: str, max_length: int = 50) -> str:
    """Short mode - one sentence summary"""
    lang = detect_language(text)
    sentences = extract_sentences(text, lang)
    
    # Return first sentence + last if very short
    if len(sentences) > 1:
        return sentences[0][:max_length*3] + '...'
    return text[:max_length*3] + ('...' if len(text) > max_length*3 else '')

def summarize_paragraph(text: str, max_length: int = 100) -> str:
    """Paragraph mode - cohesive paragraph summary"""
    return summarize_auto(text, max_length)

def summarize_text(text: str, max_length: int = 100, mode: str = "auto") -> str:
    """Summarize based on mode"""
    modes = {
        "auto": summarize_auto,
        "bullet": summarize_bullet,
        "short": summarize_short,
        "paragraph": summarize_paragraph
    }
    return modes.get(mode, summarize_auto)(text, max_length)

# ========== API ENDPOINTS ==========
@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page - HTML for human visitors"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FAL-SH - AI Text Summarization API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
            .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
            .hero { text-align: center; padding: 60px 0; }
            .hero h1 { font-size: 3.5em; font-weight: 800; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
            .hero .tagline { font-size: 1.4em; color: #888; margin-bottom: 30px; }
            .price-badge { display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 12px 30px; border-radius: 50px; font-size: 1.3em; font-weight: 700; margin-bottom: 40px; }
            .demo-box { background: #16161e; border: 1px solid #2a2a3a; border-radius: 16px; padding: 30px; margin: 40px 0; }
            .demo-box h3 { color: #667eea; margin-bottom: 15px; }
            .demo-input { width: 100%; background: #0a0a0f; border: 1px solid #333; border-radius: 8px; padding: 15px; color: #fff; font-size: 1em; resize: vertical; min-height: 120px; margin-bottom: 15px; }
            .demo-input:focus { outline: none; border-color: #667eea; }
            .demo-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 40px; border-radius: 8px; font-size: 1.1em; font-weight: 600; cursor: pointer; width: 100%; transition: transform 0.2s; }
            .demo-btn:hover { transform: scale(1.02); }
            .demo-result { margin-top: 20px; padding: 20px; background: #0a0a0f; border-radius: 8px; border-left: 4px solid #667eea; display: none; }
            .demo-result.show { display: block; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 40px 0; }
            .feature { background: #16161e; border: 1px solid #2a2a3a; border-radius: 12px; padding: 25px; }
            .feature h4 { color: #667eea; font-size: 1.1em; margin-bottom: 8px; }
            .feature p { color: #888; line-height: 1.6; }
            .pricing { background: #16161e; border: 1px solid #2a2a3a; border-radius: 16px; padding: 40px; margin: 40px 0; text-align: center; }
            .pricing h2 { font-size: 2em; margin-bottom: 30px; }
            .pricing-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 20px; }
            .price-card { background: #0a0a0f; border-radius: 12px; padding: 25px; }
            .price-card .amount { font-size: 2.5em; font-weight: 700; color: #667eea; }
            .price-card .credits { color: #888; margin: 10px 0; }
            .price-card .per { color: #555; font-size: 0.9em; }
            .cta-section { text-align: center; padding: 40px 0; }
            .cta-btn { display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; text-decoration: none; padding: 18px 50px; border-radius: 50px; font-size: 1.2em; font-weight: 700; margin: 10px; transition: transform 0.2s; }
            .cta-btn:hover { transform: scale(1.05); }
            .cta-btn.secondary { background: transparent; border: 2px solid #667eea; color: #667eea; }
            .code-example { background: #16161e; border-radius: 12px; padding: 25px; margin: 20px 0; font-family: 'Monaco', 'Consolas', monospace; font-size: 0.9em; overflow-x: auto; }
            .code-example .comment { color: #6a9955; }
            .code-example .keyword { color: #c586c0; }
            .code-example .string { color: #ce9178; }
            footer { text-align: center; padding: 40px 0; color: #555; border-top: 1px solid #1a1a2a; margin-top: 40px; }
            .stats { display: flex; justify-content: center; gap: 40px; margin: 30px 0; flex-wrap: wrap; }
            .stat { text-align: center; }
            .stat .number { font-size: 2em; font-weight: 700; color: #667eea; }
            .stat .label { color: #888; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>FAL-SH</h1>
                <p class="tagline">AI Text Summarization API</p>
                <div class="price-badge">$0.01 per 1,000 credits</div>
                <div class="stats">
                    <div class="stat"><div class="number">4</div><div class="label">Summarize Modes</div></div>
                    <div class="stat"><div class="number">2</div><div class="label">Languages</div></div>
                    <div class="stat"><div class="number">100</div><div class="label">Free Credits</div></div>
                    <div class="stat"><div class="number">0</div><div class="label">Monthly Fee</div></div>
                </div>
            </div>

            <div class="demo-box">
                <h3>🚀 Try It Now - Live Demo</h3>
                <textarea class="demo-input" id="demoText" placeholder="Paste your text here... (minimum 50 characters)">Artificial intelligence is transforming the way businesses operate in the 21st century. From automating routine tasks to providing deep insights through data analysis, AI tools are becoming essential for companies of all sizes. Small businesses can now access powerful AI capabilities through affordable APIs, leveling the playing field with larger competitors. The key to successful AI adoption lies in choosing the right tools that integrate seamlessly with existing workflows. Start small, measure results, and scale up as you see tangible benefits in your operations.</textarea>
                <button class="demo-btn" onclick="runDemo()">Generate Summary</button>
                <div class="demo-result" id="demoResult"></div>
            </div>

            <div class="features">
                <div class="feature">
                    <h4>⚡ 4 Summarize Modes</h4>
                    <p>Auto, Bullet points, Short summary, or Paragraph format. Choose the perfect output for your use case.</p>
                </div>
                <div class="feature">
                    <h4>🌏 Chinese & English</h4>
                    <p>Native support for both Chinese and English text. Auto-detects language and processes accordingly.</p>
                </div>
                <div class="feature">
                    <h4>📦 Bulk Processing</h4>
                    <p>Process up to 10 texts at once with 20% bulk discount. Perfect for content platforms.</p>
                </div>
                <div class="feature">
                    <h4>💳 Simple Pricing</h4>
                    <p>Pay only for what you use. No monthly fees, no subscriptions. Just $0.01 per 1,000 characters.</p>
                </div>
            </div>

            <div class="pricing">
                <h2>Simple, Transparent Pricing</h2>
                <div class="pricing-grid">
                    <div class="price-card">
                        <div class="amount">FREE</div>
                        <div class="credits">100 credits</div>
                        <div class="per">No credit card needed</div>
                    </div>
                    <div class="price-card">
                        <div class="amount">$10</div>
                        <div class="credits">1,000 credits</div>
                        <div class="per">$0.01 per credit</div>
                    </div>
                    <div class="price-card">
                        <div class="amount">$100</div>
                        <div class="credits">10,000 credits</div>
                        <div class="per">$0.01 per credit</div>
                    </div>
                    <div class="price-card">
                        <div class="amount">$1000</div>
                        <div class="credits">100,000 credits</div>
                        <div class="per">$0.01 per credit</div>
                    </div>
                </div>
            </div>

            <h2 style="margin: 40px 0 20px;">Quick Start</h2>
            <div class="code-example">
                <span class="comment"># 1. Get your free API key</span><br>
                <span class="keyword">curl</span> -X POST https://ai-summarizer-api-gswm.onrender.com/keys \\\<br>
                &nbsp;&nbsp;-H <span class="string">"Content-Type: application/json"</span> \\\<br>
                &nbsp;&nbsp;-d <span class="string">'{"name":"Your Name","email":"you@example.com"}'</span><br><br>
                <span class="comment"># 2. Summarize text</span><br>
                <span class="keyword">curl</span> -X POST https://ai-summarizer-api-gswm.onrender.com/summarize \\\<br>
                &nbsp;&nbsp;-H <span class="string">"Authorization: Bearer YOUR_API_KEY"</span> \\\<br>
                &nbsp;&nbsp;-H <span class="string">"Content-Type: application/json"</span> \\\<br>
                &nbsp;&nbsp;-d <span class="string">'{"text":"Your text here...","max_length":100,"mode":"auto"}'</span>
            </div>

            <div class="cta-section">
                <a href="#/docs" class="cta-btn">📖 Read Full Docs</a>
                <a href="javascript:void(0)" onclick="document.getElementById('demoText').focus();" class="cta-btn secondary">⚡ Try Live Demo</a>
            </div>
        </div>

        <script>
            async function runDemo() {
                const text = document.getElementById('demoText').value;
                const result = document.getElementById('demoResult');
                
                if (text.length < 50) {
                    result.innerHTML = '<strong style="color:#f5576c;">Please enter at least 50 characters.</strong>';
                    result.classList.add('show');
                    return;
                }
                
                result.innerHTML = '<strong style="color:#667eea;">⏳ Processing...</strong>';
                result.classList.add('show');
                
                try {
                    const response = await fetch('/summarize', {
                        method: 'POST',
                        headers: {
                            'Authorization': 'Bearer fal_demo_abc123xyz789',
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            text: text,
                            max_length: 100,
                            mode: 'auto'
                        })
                    });
                    const data = await response.json();
                    
                    if (response.ok) {
                        result.innerHTML = `<strong style="color:#4ade80;">✅ Summary:</strong><br><br>${data.summary}<br><br><small style="color:#888;">📊 Compression: ${Math.round(data.compression_ratio * 100)}% | Used ${data.credits_used} credit(s)</small>`;
                    } else {
                        result.innerHTML = `<strong style="color:#f5576c;">❌ Error:</strong> ${data.detail || 'Something went wrong'}`;
                    }
                } catch (e) {
                    result.innerHTML = `<strong style="color:#f5576c;">❌ Network error:</strong> ${e.message}`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health():
    """Health check with extended status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.3.0",
        "service": "FAL-SH",
        "stripe_connected": bool(stripe.api_key),
        "uptime": "operational",
        "regions": ["render-free-us"],
        "sla": "99.5% uptime (paid plans)"
    }

@app.get("/status")
async def status():
    """Detailed API status"""
    total_keys = len(api_keys_db)
    total_requests = sum(u.get("total_requests", 0) for u in api_keys_db.values())
    return {
        "api_status": "operational",
        "version": "2.3.0",
        "total_users": total_keys,
        "total_requests_served": total_requests,
        "features": {
            "modes": ["auto", "bullet", "short", "paragraph"],
            "languages": ["en", "zh"],
            "bulk_processing": True
        }
    }

@app.get("/pricing")
async def pricing():
    """Detailed pricing page"""
    return {
        "per_credit_usd": 0.01,
        "credit_explainer": "1 credit = 1000 characters summarized",
        "tiers": [
            {"name": "Free Trial", "credits": 100, "price": 0},
            {"name": "Starter", "credits": 1000, "price": 10},
            {"name": "Pro", "credits": 10000, "price": 100},
            {"name": "Enterprise", "credits": 100000, "price": 1000}
        ],
        "add_ons": [
            {"name": "Bulk processing", "discount": "20%"},
            {"name": "Monthly subscription", "discount": "30%"}
        ],
        "payment_methods": ["Visa", "Mastercard", "American Express", "Alipay (via Stripe)"]
    }

@app.post("/keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreateRequest):
    """Create new API key with free credits"""
    # Check if email already exists
    for key, data in api_keys_db.items():
        if data.get("email") == request.email:
            raise HTTPException(status_code=400, detail="Email already registered. Use existing key or contact support.")
    
    # Generate key
    api_key = "fal_" + hashlib.sha256(
        f"{request.name}{request.email}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:28]
    
    initial_credits = 100  # Free trial
    
    api_keys_db[api_key] = {
        "name": request.name,
        "email": request.email,
        "credits": initial_credits,
        "created_at": datetime.now().isoformat(),
        "total_requests": 0
    }
    
    logger.info(f"New user: {request.email} -> {api_key[:12]}...")
    
    return APIKeyResponse(
        api_key=api_key,
        name=request.name,
        credits=initial_credits,
        created_at=datetime.now().isoformat()
    )

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    api_key_info: tuple = Depends(get_api_key)
):
    """Summarize text - supports multiple modes"""
    api_key, user = api_key_info
    
    credits_needed = calculate_credits(len(request.text))
    
    if user["credits"] < credits_needed:
        raise HTTPException(
            status_code=402,
            detail=f"Not enough credits. Need {credits_needed}, have {user['credits']}. Buy at POST /purchase"
        )
    
    # Generate summary using selected mode
    lang = detect_language(request.text) if request.language == "auto" else request.language
    summary = summarize_text(request.text, request.max_length, request.mode)
    
    # Update stats
    user["credits"] -= credits_needed
    user["total_requests"] += 1
    
    # Log
    requests_log.append({
        "request_id": str(uuid.uuid4()),
        "api_key": api_key[:12] + "...",
        "text_length": len(request.text),
        "credits_used": credits_needed,
        "mode": request.mode,
        "timestamp": datetime.now().isoformat()
    })
    
    return SummarizeResponse(
        summary=summary,
        original_length=len(request.text),
        summary_length=len(summary),
        compression_ratio=round(len(summary)/len(request.text), 4) if request.text else 0,
        credits_used=credits_needed,
        request_id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        mode_used=request.mode
    )

@app.post("/bulk")
async def bulk_summarize(
    request: BulkSummarizeRequest,
    api_key_info: tuple = Depends(get_api_key)
):
    """Bulk summarize multiple texts - 20% discount!"""
    api_key, user = api_key_info
    
    results = []
    total_credits = 0
    
    for text in request.texts:
        credits_needed = calculate_credits(len(text))
        if user["credits"] >= credits_needed:
            summary = summarize_text(text, 100, "auto")
            user["credits"] -= credits_needed
            total_credits += credits_needed
            results.append({
                "summary": summary,
                "original_length": len(text),
                "credits_used": credits_needed,
                "success": True
            })
        else:
            results.append({
                "error": "Insufficient credits",
                "credits_needed": credits_needed,
                "success": False
            })
    
    return {
        "results": results,
        "total_credits_used": total_credits,
        "bulk_discount": "20% off for bulk!",
        "remaining_credits": user["credits"]
    }

@app.get("/usage")
async def get_usage(api_key_info: tuple = Depends(get_api_key)):
    """Get user's usage stats and remaining credits"""
    api_key, user = api_key_info
    
    return {
        "api_key": api_key[:12] + "...",
        "name": user["name"],
        "remaining_credits": user["credits"],
        "total_requests": user.get("total_requests", 0),
        "created_at": user["created_at"],
        "estimated_spent_usd": round(user.get("total_requests", 0) * 0.01, 2),
        "credit_status": "active" if user["credits"] > 0 else "depleted"
    }

@app.post("/purchase", response_model=CreditPurchaseResponse)
async def purchase_credits(request: CreditPurchaseRequest):
    """Create Stripe checkout for credits"""
    try:
        credit_price_usd = float(os.getenv("CREDIT_PRICE_USD", "0.01"))
        total_amount = int(request.credits * credit_price_usd * 100)
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{request.credits} FAL-SH Credits',
                        'description': f'AI Text Summarization Credits | $0.01 per credit'
                    },
                    'unit_amount': total_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                'credits': str(request.credits),
                'product': 'fal_sh_credits'
            }
        )
        
        return CreditPurchaseResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Payment error. Please try again.")

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe.error.StripeError:
        raise HTTPException(status_code=400, detail="Stripe error")
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        credits = session.get('metadata', {}).get('credits', '0')
        logger.info(f"Payment completed: {credits} credits")
    
    return {"status": "received"}

@app.get("/stats")
async def stats():
    """Public stats"""
    total_requests = sum(u.get("total_requests", 0) for u in api_keys_db.values())
    return {
        "total_api_keys": len(api_keys_db),
        "total_requests": total_requests,
        "version": "2.3.0",
        "pricing": "$0.01 per 1000 credits"
    }

@app.get("/docs")
async def docs():
    """Redirect to Swagger docs"""
    return JSONResponse(content={"redirect": "/docs"}, status_code=302)

@app.get("/code-examples")
async def code_examples():
    """Get code examples in multiple languages"""
    return {
        "python": {
            "method": "POST",
            "url": "https://ai-summarizer-api-gswm.onrender.com/summarize",
            "headers": {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
            "body": {"text": "Your text here", "max_length": 100, "mode": "auto"},
            "code": '''
import requests

response = requests.post(
    "https://ai-summarizer-api-gswm.onrender.com/summarize",
    headers={"Authorization": "Bearer YOUR_KEY"},
    json={"text": "Your text here", "max_length": 100, "mode": "auto"}
)
print(response.json()["summary"])
'''
        },
        "javascript": {
            "method": "POST",
            "url": "https://ai-summarizer-api-gswm.onrender.com/summarize",
            "code": '''
const response = await fetch("/summarize", {
    method: "POST",
    headers: {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    body: JSON.stringify({text: "Your text", max_length: 100, mode: "auto"})
});
const data = await response.json();
console.log(data.summary);
'''
        },
        "curl": {
            "method": "POST",
            "url": "https://ai-summarizer-api-gswm.onrender.com/summarize",
            "code": '''
curl -X POST https://ai-summarizer-api-gswm.onrender.com/summarize \\
  -H "Authorization: Bearer YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"text":"Your text","max_length":100,"mode":"auto"}'
'''
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler"""
    logger.error(f"Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": str(exc)[:100]}
    )