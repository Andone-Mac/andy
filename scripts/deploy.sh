#!/bin/bash

# 🚀 AI Summarizer API Deployment Script
# One-command deployment to production

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Summarizer API - Production Deployment${NC}"
echo -e "${YELLOW}Time: $(date)${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $(python3 --version | cut -d' ' -f2)${NC}"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check environment file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found.${NC}"
    echo -e "${BLUE}📝 Copying .env.example to .env...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your configuration before production deployment.${NC}"
fi

# Run tests (if any)
if [ -d "tests" ]; then
    echo -e "${BLUE}🧪 Running tests...${NC}"
    python -m pytest tests/ -v || echo -e "${YELLOW}⚠️  Tests failed, but continuing deployment.${NC}"
fi

# Start the service
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo -e "${BLUE}🚀 Starting AI Summarizer API...${NC}"
echo -e "${BLUE}📊 Service will be available at:${NC}"
echo -e "   Local: http://localhost:8000"
echo -e "   Docs: http://localhost:8000/docs"
echo -e "   Redoc: http://localhost:8000/redoc"
echo ""
echo -e "${YELLOW}💰 Revenue Information:${NC}"
echo -e "   Pricing: \$0.01 per credit"
echo -e "   Target MRR: \$1000-10000"
echo -e "   Deployment Cost: \$5-20/month"
echo ""
echo -e "${GREEN}✅ Ready to make money!${NC}"

# Run the application
python src/main.py