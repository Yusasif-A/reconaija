"""
FastAPI Backend for BCT Hackathon
Naija Yelp Review Agent - RecoNaija
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
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
    user_id: str = Field(
        ...,
        description="User ID from demo users OR 'cold_start' for new user",
        examples=["user_001", "user_042", "user_123"]
    )
    persona_text: str = Field(
        ...,
        description="Persona override (e.g., 'Pidgin Pro', 'Formal English') or user description for cold-start",
        examples=[
            "Pidgin Pro",
            "Formal English",
            "I'm a Gen Z foodie who loves trying new restaurants in Lagos"
        ]
    )
    product_name: str = Field(
        ...,
        description="Name of the restaurant/business to review",
        examples=["Chicken Republic", "Mama Cass", "The Place", "Cafe Neo"]
    )
    product_category: str = Field(
        ...,
        description="Category of the business",
        examples=["Fast Food", "Nigerian Restaurant", "Bar & Lounge", "Coffee Shop"]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "user_id": "user_001",
                    "persona_text": "Pidgin Pro",
                    "product_name": "Chicken Republic",
                    "product_category": "Fast Food"
                },
                {
                    "user_id": "user_042",
                    "persona_text": "Formal English",
                    "product_name": "Mama Cass",
                    "product_category": "Nigerian Restaurant"
                }
            ]
        }

class TaskAResponse(BaseModel):
    stars: int = Field(..., description="Star rating (1-5)", examples=[4])
    review_text: str = Field(
        ...,
        description="Generated review text",
        examples=["This place dey burst brain! The jollof rice sweet die and the service sharp sharp. I go definitely come back."]
    )
    user_style_summary: str = Field(
        ...,
        description="Summary of user's writing style",
        examples=["User writes in Nigerian Pidgin, averages 3.2 stars, focuses on food quality and value"]
    )

class TaskBRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="User ID from demo users OR 'cold_start' for semantic search",
        examples=["user_001", "user_042", "cold_start"]
    )
    persona_text: str = Field(
        ...,
        description="User preferences description (required for cold_start, optional for existing users)",
        examples=[
            "I want affordable Nigerian food in Surulere",
            "Looking for upscale dining in Victoria Island",
            "Need a good coffee shop in Lekki for work meetings"
        ]
    )
    top_k: int = Field(
        default=5,
        description="Number of recommendations to return (3, 5, 7, or 10)",
        examples=[3, 5, 7]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "user_id": "user_001",
                    "persona_text": "I want something similar to what I usually like",
                    "top_k": 5
                },
                {
                    "user_id": "cold_start",
                    "persona_text": "I want affordable Nigerian food in Surulere",
                    "top_k": 3
                },
                {
                    "user_id": "cold_start",
                    "persona_text": "Looking for upscale dining and cocktails in Victoria Island",
                    "top_k": 5
                }
            ]
        }

class TaskBResponse(BaseModel):
    recommendations: list[dict] = Field(
        ...,
        description="List of recommended businesses",
        examples=[[
            {
                "name": "Mama Cass",
                "category": "Nigerian Restaurant",
                "reason": "This restaurant serves authentic Nigerian buffet with excellent jollof rice and affordable prices, perfect for your taste preferences.",
                "image_url": ""
            }
        ]]
    )
    mode: str = Field(
        ...,
        description="Recommendation mode used",
        examples=["history_based", "cold_start"]
    )

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
    1. Fetch user's review history (if user_id is not 'cold_start')
    2. Analyze their writing style (Pidgin level, tone, topics)
    3. Fetch target business info
    4. Generate review matching their style + Nigerian context
    
    **Examples:**
    - Existing user: `user_id="user_001"`, `persona_text="Pidgin Pro"`, `product_name="Chicken Republic"`
    - Cold start: `user_id="cold_start"`, `persona_text="I'm a Gen Z foodie"`, `product_name="Mama Cass"`
    """
    result = await run_task_a(request)
    return result

@app.post("/recommend", response_model=TaskBResponse)
async def recommend(request: TaskBRequest):
    """
    Task B: Recommend restaurants based on user preferences

    The agent will:
    - If user_id is a real user (e.g., "user_001"): Use review history (SQL queries)
    - If user_id is "cold_start": Use semantic search (ChromaDB embeddings)
    - Rank and explain recommendations with Nigerian context
    
    **Examples:**
    - History-based: `user_id="user_001"`, `persona_text="Similar to what I like"`, `top_k=5`
    - Cold-start: `user_id="cold_start"`, `persona_text="Affordable Nigerian food in Surulere"`, `top_k=3`
    
    **Note:** For cold-start testing, always use `user_id="cold_start"` and provide detailed preferences in `persona_text`
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
