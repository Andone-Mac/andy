"""
AI Summarizer API - Production Ready
FastAPI application with Stripe monetization
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import uuid
from datetime import datetime, timedelta
import os
import stripe
from dotenv import load_dotenv
import hashlib
import json
import logging

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
    title="AI Summarizer API",
    description="Monetized AI text summarization service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ========== MODELS ==========
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=50000)
    max_length: int = Field(100, ge=50, le=500)
    language: Optional[str] = "en"

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
    name: str
    email: str

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

# ========== IN-MEMORY STORAGE (REPLACE WITH DATABASE IN PRODUCTION) ==========
# In production, use PostgreSQL/Redis
api_keys_db: Dict[str, dict] = {}
requests_log: List[dict] = []
users_db: Dict[str, dict] = {}

# Demo user for testing
DEMO_API_KEY = "demo_key_" + hashlib.sha256(b"demo").hexdigest()[:16]
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
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    user = api_keys_db[api_key]
    if user["credits"] <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits. Please purchase more credits.")
    
    return api_key, user

def calculate_credits(text_length: int) -> int:
    """Calculate credits based on text length"""
    credits_per_1000_chars = int(os.getenv("CREDITS_PER_CHARACTER", 1))
    return max(1, (text_length // 1000) * credits_per_1000_chars)

def summarize_text(text: str, max_length: int = 100) -> str:
    """
    Summarize text using a simple algorithm.
    In production, replace with AI model (OpenAI, Anthropic, etc.)
    """
    # Simple extractive summarization: take first, middle, last sentences
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    if len(sentences) <= 3:
        return text
    
    important_indices = [0, len(sentences) // 2, -1]
    important_sentences = [sentences[i] for i in important_indices if i < len(sentences)]
    
    summary = '. '.join(important_sentences) + '.'
    
    # Truncate if too long
    words = summary.split()
    if len(words) > max_length:
        summary = ' '.join(words[:max_length]) + '...'
    
    return summary

# ========== API ENDPOINTS ==========
@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "AI Summarizer API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "summarize": "POST /summarize",
            "create_key": "POST /keys",
            "purchase_credits": "POST /purchase",
            "stats": "GET /stats",
            "health": "GET /health",
            "webhook": "POST /webhook/stripe"
        },
        "pricing": f"${os.getenv('CREDIT_PRICE_USD', '0.01')} per credit",
        "demo_api_key": DEMO_API_KEY,
        "note": "For production, replace in-memory storage with database"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stripe_connected": stripe.api_key is not None
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    api_key_info: tuple = Depends(get_api_key)
):
    """Summarize text using credits"""
    api_key, user = api_key_info
    
    # Calculate credits needed
    credits_needed = calculate_credits(len(request.text))
    
    # Check if user has enough credits
    if user["credits"] < credits_needed:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {credits_needed}, have {user['credits']}"
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
        "api_key": api_key[:8] + "...",
        "text_length": len(request.text),
        "credits_used": credits_needed,
        "timestamp": datetime.now().isoformat()
    })
    
    return SummarizeResponse(
        summary=summary,
        original_length=len(request.text),
        summary_length=len(summary),
        compression_ratio=len(summary) / len(request.text) if len(request.text) > 0 else 0,
        credits_used=credits_needed,
        request_id=request_id,
        timestamp=datetime.now().isoformat()
    )

@app.post("/keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreateRequest):
    """Create a new API key with free trial credits"""
    # Generate unique API key
    api_key = "sk_" + hashlib.sha256(
        f"{request.name}{request.email}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:32]
    
    # Initial free credits
    initial_credits = 100  # Free trial credits
    
    # Store user
    api_keys_db[api_key] = {
        "name": request.name,
        "email": request.email,
        "credits": initial_credits,
        "created_at": datetime.now().isoformat(),
        "total_requests": 0
    }
    
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
                        'name': f'{request.credits} API Credits',
                        'description': f'Credits for AI Summarizer API'
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
                'product': 'api_credits'
            }
        )
        
        return CreditPurchaseResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (payment success, etc.)"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extract metadata
        credits = int(session['metadata'].get('credits', 0))
        customer_email = session.get('customer_details', {}).get('email')
        
        # In production: find user by email and add credits
        # For now, log the purchase
        logger.info(f"Purchase completed: {credits} credits for {customer_email}")
        
        # TODO: Update user's credit balance in database
        
    return {"status": "webhook processed"}

@app.get("/stats")
async def get_stats(api_key_info: tuple = Depends(get_api_key)):
    """Get user statistics"""
    api_key, user = api_key_info
    
    credit_price = float(os.getenv("CREDIT_PRICE_USD", "0.01"))
    estimated_spent = (user.get("total_requests", 0) * credit_price)
    
    return UserStats(
        total_requests=user.get("total_requests", 0),
        total_credits_used=user.get("total_requests", 0),  # Simplified
        remaining_credits=user["credits"],
        estimated_spent=estimated_spent
    )

@app.get("/admin/keys")
async def list_api_keys(admin_key: str = Header(None)):
    """Admin endpoint to list all API keys (sanitized)"""
    if admin_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sanitized_keys = []
    for key, data in api_keys_db.items():
        sanitized_keys.append({
            "key": key[:8] + "..." + key[-4:],
            "name": data["name"],
            "credits": data["credits"],
            "created_at": data["created_at"],
            "total_requests": data.get("total_requests", 0)
        })
    
    return {"keys": sanitized_keys, "count": len(sanitized_keys)}

# ========== MAIN ==========
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    
    print("=" * 50)
    print("🚀 AI Summarizer API - Production Ready")
    print(f"📊 Version: 2.0.0")
    print(f"💰 Pricing: ${os.getenv('CREDIT_PRICE_USD', '0.01')} per credit")
    print(f"🔑 Demo API Key: {DEMO_API_KEY}")
    print(f"🌐 Docs: http://localhost:{port}/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=port)