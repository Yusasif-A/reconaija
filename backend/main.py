"""
FastAPI Backend for BCT Hackathon
Naija Yelp Review Agent - RecoNaija
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.task_a_agent import run_task_a
from agents.task_b_agent import run_task_b
from database.db import get_demo_users

app = FastAPI(
    title="RecoNaija API",
    description="Nigerian Yelp Review Agent - BCT Hackathon",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request/Response Models ====================

class TaskARequest(BaseModel):
    user_id: str          # selected from dropdown OR "cold_start"
    persona_text: str     # free text description (optional, for cold-start)
    product_name: str     # name of the restaurant/place to review
    product_category: str # e.g. "Restaurant", "Fast Food", "Bar", "Cafe"

class TaskAResponse(BaseModel):
    stars: int
    review_text: str
    user_style_summary: str  # e.g. "User writes in pidgin, avg 2.3 stars"

class TaskBRequest(BaseModel):
    user_id: str          # selected from dropdown OR "cold_start"
    persona_text: str     # free text (for cold-start)
    top_k: int = 5        # number of recommendations to return

class TaskBResponse(BaseModel):
    recommendations: list[dict]  # [{name, category, reason}]
    mode: str  # "history_based" or "cold_start"

# ==================== Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RecoNaija API - Nigerian Yelp Review Agent",
        "version": "1.0.0",
        "endpoints": {
            "generate_review": "POST /generate-review",
            "recommend": "POST /recommend",
            "demo_users": "GET /demo-users",
            "health": "GET /health"
        }
    }

@app.post("/generate-review", response_model=TaskAResponse)
async def generate_review(request: TaskARequest):
    """
    Task A: Generate a review simulating how a specific user would review a place

    The agent will:
    1. Fetch user's review history
    2. Analyze their writing style (Pidgin level, tone, topics)
    3. Fetch target business info
    4. Generate review matching their style + Nigerian context
    """
    result = await run_task_a(request)
    return result

@app.post("/recommend", response_model=TaskBResponse)
async def recommend(request: TaskBRequest):
    """
    Task B: Recommend restaurants based on user preferences

    The agent will:
    - If user_id provided: Use review history (SQL queries)
    - If cold_start: Use semantic search (FAISS embeddings)
    - Rank and explain recommendations with Nigerian context
    """
    result = await run_task_b(request)
    return result

@app.get("/demo-users")
async def get_demo_users_list():
    """
    Get list of curated Nigerian-themed demo users for dropdown

    Returns users with display names like:
    - The Lagos Foodie
    - The Budget King
    - The Pidgin Pro
    - etc.
    """
    users = get_demo_users()
    return users

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RecoNaija API",
        "database": "connected"
    }

# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("🚀 RecoNaija API starting...")
    print("🇳🇬 Nigerian Yelp Review Agent - BCT Hackathon")
    print("="*50)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
