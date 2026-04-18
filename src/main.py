"""
AI Summarizer API v2.1 - Improved Version
FastAPI application with Stripe monetization
Optimized for FAL-SH project
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
    title="FAL-SH: AI Summarizer API",
    description="Fast, affordable text summarization API for developers. $0.01 per 1000 credits.",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "FAL-SH Support",
        "url": "https://ai-summarizer-api-gswm.onrender.com"
    }
)

# CORS middleware - more restrictive
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ========== MODELS ==========
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    max_length: int = Field(100, ge=20, le=500)
    language: Optional[str] = "en"
    
    @field_validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v

class SummarizeResponse(BaseModel):
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
    credits_used: int
    request_id: str
    timestamp: str

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

class UserStats(BaseModel):
    total_requests: int
    total_credits_used: int
    remaining_credits: int
    estimated_spent: float

class BulkSummarizeRequest(BaseModel):
    texts: List[str] = Field(..., max_length=10)

# ========== IN-MEMORY STORAGE ==========
api_keys_db: Dict[str, dict] = {}
requests_log: List[dict] = []

# Demo user with fixed key for easy testing
DEMO_API_KEY = "fal_demo_abc123xyz789"
api_keys_db[DEMO_API_KEY] = {
    "name": "Demo User",
    "credits": 1000,
    "created_at": datetime.now().isoformat(),
    "total_requests": 0,
    "email": "demo@example.com"
}

# ========== HELPER FUNCTIONS ==========
def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate API key and return user info"""
    api_key = credentials.credentials
    if api_key not in api_keys_db:
        # Try to find by prefix match
        for key in api_keys_db:
            if key.startswith(api_key[:20]):
                api_key = key
                break
        else:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    user = api_keys_db[api_key]
    if user["credits"] <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits. Please purchase more credits.")
    
    return api_key, user

def calculate_credits(text_length: int) -> int:
    """Calculate credits based on text length - more efficient"""
    return max(1, text_length // 1000)

def extract_sentences(text: str) -> List[str]:
    """Extract sentences from text"""
    sentences = re.split(r'[。.!?]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

def score_sentence(sentence: str, keywords: List[str]) -> float:
    """Score sentence importance based on keyword frequency and position"""
    score = 0.0
    
    # Position scoring - first and last sentences are important
    if sentence == extract_sentences(api_keys_db.get('__text', ''))[0] if '__text' in api_keys_db else '':
        score += 2.0
    if sentence == extract_sentences(api_keys_db.get('__text', ''))[-1] if '__text' in api_keys_db else '':
        score += 1.5
    
    # Keyword scoring
    for keyword in keywords:
        if keyword.lower() in sentence.lower():
            score += 1.0
    
    # Length scoring - prefer medium length sentences
    word_count = len(sentence.split())
    if 10 <= word_count <= 30:
        score += 1.0
    elif word_count > 50:
        score -= 0.5
    
    return score

def summarize_text_advanced(text: str, max_length: int = 100, max_sentences: int = 3) -> str:
    """
    Advanced extractive summarization with sentence scoring.
    Returns the most important sentences maintaining original order.
    """
    sentences = extract_sentences(text)
    
    if len(sentences) <= max_sentences:
        return text
    
    # Extract keywords (simple frequency-based)
    words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{3,}\b', text.lower())
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', '的', '是', '在', '了', '和', '或', '这', '那'}
    for sw in stop_words:
        word_freq.pop(sw, None)
    
    # Get top keywords
    keywords = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:10]
    
    # Score sentences
    scored = []
    for i, sentence in enumerate(sentences):
        score = score_sentence(sentence, keywords)
        scored.append((score, i, sentence))
    
    # Sort by score descending
    scored.sort(key=lambda x: (-x[0], x[1]))
    
    # Take top sentences but maintain original order
    top_indices = set(idx for _, idx, _ in scored[:max_sentences])
    selected = [(idx, sentence) for score, idx, sentence in scored if idx in top_indices]
    selected.sort(key=lambda x: x[0])
    
    result = '。'.join(s for _, s in selected)
    
    # Ensure we don't exceed max_length
    words = result.split()
    if len(words) > max_length:
        result = ' '.join(words[:max_length]) + '...'
    
    return result if result.endswith('.') or result.endswith('。') else result + '。'

def summarize_text(text: str, max_length: int = 100) -> str:
    """Wrapper for backward compatibility"""
    return summarize_text_advanced(text, max_length)

# ========== API ENDPOINTS ==========
@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "FAL-SH: AI Summarizer API",
        "version": "2.1.0",
        "status": "operational",
        "description": "Fast, affordable text summarization for developers",
        "endpoints": {
            "health": "GET /health",
            "summarize": "POST /summarize",
            "bulk_summarize": "POST /bulk",
            "create_key": "POST /keys",
            "purchase_credits": "POST /purchase",
            "usage": "GET /usage",
            "pricing": "GET /pricing",
            "docs": "GET /docs"
        },
        "pricing": {
            "per_credit": f"${os.getenv('CREDIT_PRICE_USD', '0.01')}",
            "per_1000_chars": "1 credit"
        },
        "demo_api_key": DEMO_API_KEY,
        "free_trial_credits": 100
    }

@app.get("/health")
async def health():
    """Health check endpoint with more details"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stripe_connected": bool(stripe.api_key),
        "version": "2.1.0",
        "service": "FAL-SH"
    }

@app.get("/pricing")
async def pricing():
    """Public pricing information"""
    return {
        "per_credit_usd": float(os.getenv("CREDIT_PRICE_USD", "0.01")),
        "per_1000_chars": 1,
        "minimum_purchase": 100,
        "maximum_purchase": 100000,
        "currency": "USD",
        "methods": ["Stripe Checkout (card)"]
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    api_key_info: tuple = Depends(get_api_key)
):
    """Summarize text using credits - optimized version"""
    api_key, user = api_key_info
    
    # Calculate credits needed
    credits_needed = calculate_credits(len(request.text))
    
    # Check if user has enough credits
    if user["credits"] < credits_needed:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {credits_needed}, have {user['credits']}. Please purchase more at POST /purchase"
        )
    
    # Generate summary
    summary = summarize_text(request.text, request.max_length)
    
    # Deduct credits and update stats
    user["credits"] -= credits_needed
    user["total_requests"] = user.get("total_requests", 0) + 1
    
    # Log request
    request_id = str(uuid.uuid4())
    requests_log.append({
        "request_id": request_id,
        "api_key": api_key[:12] + "...",
        "text_length": len(request.text),
        "summary_length": len(summary),
        "credits_used": credits_needed,
        "timestamp": datetime.now().isoformat()
    })
    
    return SummarizeResponse(
        summary=summary,
        original_length=len(request.text),
        summary_length=len(summary),
        compression_ratio=round(len(summary) / len(request.text), 4) if len(request.text) > 0 else 0,
        credits_used=credits_needed,
        request_id=request_id,
        timestamp=datetime.now().isoformat()
    )

@app.post("/bulk")
async def bulk_summarize(
    request: BulkSummarizeRequest,
    api_key_info: tuple = Depends(get_api_key)
):
    """Bulk summarize multiple texts"""
    api_key, user = api_key_info
    
    results = []
    total_credits = 0
    
    for text in request.texts:
        credits_needed = calculate_credits(len(text))
        if user["credits"] >= credits_needed:
            summary = summarize_text(text, 100)
            user["credits"] -= credits_needed
            total_credits += credits_needed
            results.append({
                "summary": summary,
                "original_length": len(text),
                "credits_used": credits_needed
            })
        else:
            results.append({
                "error": "Insufficient credits",
                "original_length": len(text)
            })
    
    return {
        "results": results,
        "total_credits_used": total_credits,
        "remaining_credits": user["credits"]
    }

@app.get("/usage")
async def get_usage(
    api_key_info: tuple = Depends(get_api_key)
):
    """Get user's usage statistics"""
    api_key, user = api_key_info
    
    total_credits_used = user.get("total_requests", 0) * 1  # Simplified
    
    return {
        "api_key": api_key[:12] + "...",
        "name": user["name"],
        "remaining_credits": user["credits"],
        "total_requests": user.get("total_requests", 0),
        "created_at": user["created_at"],
        "estimated_spent_usd": round(user.get("total_requests", 0) * 0.01, 2)
    }

@app.post("/keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreateRequest):
    """Create a new API key with free trial credits"""
    # Generate unique API key
    api_key = "fal_" + hashlib.sha256(
        f"{request.name}{request.email}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:28]
    
    # Initial free credits
    initial_credits = 100  # Free trial
    
    # Store user
    api_keys_db[api_key] = {
        "name": request.name,
        "email": request.email,
        "credits": initial_credits,
        "created_at": datetime.now().isoformat(),
        "total_requests": 0
    }
    
    logger.info(f"New API key created for {request.email}: {api_key[:12]}...")
    
    return APIKeyResponse(
        api_key=api_key,
        name=request.name,
        credits=initial_credits,
        created_at=datetime.now().isoformat()
    )

@app.post("/purchase", response_model=CreditPurchaseResponse)
async def purchase_credits(request: CreditPurchaseRequest):
    """Create Stripe checkout session for credit purchase"""
    try:
        credit_price_usd = float(os.getenv("CREDIT_PRICE_USD", "0.01"))
        total_amount = int(request.credits * credit_price_usd * 100)  # Convert to cents
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{request.credits} FAL-SH API Credits',
                        'description': f'AI Summarizer API Credits - $0.01 per credit'
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
                'product': 'fal_sh_api_credits'
            }
        )
        
        return CreditPurchaseResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail="Stripe error")
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        credits = session.get('metadata', {}).get('credits', '0')
        logger.info(f"Payment successful: {credits} credits purchased")
        # Here you would update the user's credit balance
        # This requires storing session-to-user mapping
    
    return {"status": "received"}

@app.get("/stats")
async def stats():
    """Public statistics about the API"""
    total_requests = sum(u.get("total_requests", 0) for u in api_keys_db.values())
    return {
        "total_api_keys": len(api_keys_db),
        "total_requests": total_requests,
        "version": "2.1.0"
    }

@app.get("/docs")
async def docs_redirect():
    """Redirect to Swagger docs"""
    return {"redirect": "/docs"}