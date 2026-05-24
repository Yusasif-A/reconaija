# DSN x BCT LLM Agent Hackathon — Full Build Specification

> This document is a complete technical specification for building the DSN x BCT hackathon submission.
> It covers the frontend, backend, database, agent architecture, tools, middleware, code structure,
> and deployment. Give this to any LLM and it will understand exactly what to build.

---

## 1. Overview

We are building a **single web application** with two tasks:

- **Task A — User Modeling**: Given a user and a product/place, simulate the review that user would write (star rating + text)
- **Task B — Recommendation**: Given a user or a persona description, return personalized ranked recommendations

The app must be:
- Containerized with Docker
- Deployed to Hugging Face Spaces or Railway
- Backed by a FastAPI Python backend
- Fronted by a custom HTML/CSS/JS frontend (React or plain HTML — your choice)
- Powered by LangChain agents 
- open dataset as the data source

### Data Access Strategy (Important — Read This First)

Not everything needs embeddings or vector search. Here is the simple rule:

| Situation | What to use | Why |
|---|---|---|
| Task A — any user | Plain SQL only | User has history, just fetch it |
| Task B — existing user | Plain SQL only | Fetch history, find unvisited places |
| Task B — cold start (free text) | SQL + FAISS embeddings | No user_id to look up, must search by meaning |

**Only cold-start users need embeddings.** Everything else is a plain SQLite query.
The FAISS index stores only business descriptions and is used only when a user types a free-text persona with no history. It never mixes with user review data.

---

## 2. Dataset

### Source
Download from: **https://www.yelp.com/dataset**
- Fill the form (name, email, use = "academic research")
- Download the JSON files

### Files Needed
| File | What it contains |
|---|---|
| `yelp_academic_dataset_review.json` | All user reviews (stars, text, user_id, business_id, date) |
| `yelp_academic_dataset_business.json` | Business info (name, category, location, stars) |
| `yelp_academic_dataset_user.json` | User info (user_id, review_count, average_stars) |

### Data Loading
At startup, load a **subset** of the data into SQLite (full dataset is too large to load entirely).

```python
# Recommended subset sizes for a hackathon
- reviews: 500,000 rows
- businesses: 150,000 rows
- users: 100,000 rows
```

### SQLite Schema

```sql
-- users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    review_count INTEGER,
    average_stars REAL,
    display_name TEXT  -- friendly label e.g. "The Harsh Critic"
);

-- businesses table
CREATE TABLE businesses (
    business_id TEXT PRIMARY KEY,
    name TEXT,
    categories TEXT,
    city TEXT,
    state TEXT,
    stars REAL,
    review_count INTEGER
);

-- reviews table
CREATE TABLE reviews (
    review_id TEXT PRIMARY KEY,
    user_id TEXT,
    business_id TEXT,
    stars INTEGER,
    text TEXT,
    date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (business_id) REFERENCES businesses(business_id)
);
```

### Curated Demo Users
Pre-select 8–10 interesting users from the dataset and tag them with display names for the dropdown:

```python
DEMO_USERS = [
    {"user_id": "abc123", "display_name": "The Harsh Critic",    "description": "Avg 1.8 stars, very blunt"},
    {"user_id": "def456", "display_name": "The Hype Man",        "description": "Avg 4.9 stars, loves everything"},
    {"user_id": "ghi789", "display_name": "The Detailist",       "description": "Long reviews, notices everything"},
    {"user_id": "jkl012", "display_name": "The Casual Guy",      "description": "Short reviews, rarely rates"},
    {"user_id": "mno345", "display_name": "The Value Hunter",    "description": "Always mentions price/value"},
    {"user_id": "pqr678", "display_name": "The Service Checker", "description": "Only cares about staff & speed"},
]
```

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend API | FastAPI (Python) |
| Agent Framework | LangGraph (StateGraph) |
| LLM | Groq + LLaMA 3.3 70B (free) OR OpenAI GPT-4o |
| Database | SQLite (loaded from Yelp JSON at startup) |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) |
| Vector Search | FAISS (Task B cold-start only) |
| Containerization | Docker + Docker Compose |
| Deployment | Hugging Face Spaces OR Railway |

### Why React over plain HTML
React with Tailwind gives you a professional UI fast — components, state management, loading spinners, tab switching all handled cleanly. Plain HTML works but you'll manually manage DOM updates and state which gets messy fast. Use React.

### Why LangGraph over `create_agent`
LangGraph lets you define every step of your agent as explicit nodes and edges. This is what judges want to see — a visible, documented agentic workflow. `create_agent` hides the logic in a black box. LangGraph is what `create_agent` runs on underneath anyway, so you're just getting closer to the metal.

---

## 4. Project Folder Structure

```
bct-hackathon/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── task_a_agent.py      # User Modeling agent
│   │   └── task_b_agent.py      # Recommendation agent
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── user_tools.py        # fetch_user_reviews, get_user_profile
│   │   ├── business_tools.py    # fetch_business_info, search_businesses
│   │   └── recommendation_tools.py  # vector_search, rank_candidates
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── nigerian_localization.py  # Nigerian style post-processor
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                # SQLite connection and queries
│   │   └── load_data.py         # Script to load Yelp JSON into SQLite
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── vector_store.py      # FAISS index builder and searcher
│   ├── config.py                # API keys, model names, paths
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root component, tab switching
│   │   ├── components/
│   │   │   ├── TaskA.jsx        # User Modeling tab
│   │   │   ├── TaskB.jsx        # Recommendation tab
│   │   │   ├── UserDropdown.jsx # Shared user selector
│   │   │   ├── StarRating.jsx   # Star display component
│   │   │   └── ReviewCard.jsx   # Output card component
│   │   └── api.js               # All fetch calls to FastAPI
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── data/
│   ├── yelp_reviews.db          # SQLite database (generated at setup)
│   └── faiss_index/             # FAISS vector index (generated at setup)
│
├── scripts/
│   └── setup_data.py            # One-time script: load JSON → SQLite → FAISS
│
├── docker-compose.yml
├── backend/Dockerfile
├── frontend/Dockerfile
└── README.md
```

---

## 5. Backend — FastAPI

### `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.task_a_agent import run_task_a
from agents.task_b_agent import run_task_b

app = FastAPI(title="BCT Hackathon API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Request/Response Models ---

class TaskARequest(BaseModel):
    user_id: str          # selected from dropdown OR None if using persona
    persona_text: str     # free text description (optional)
    product_name: str     # name of the place/product to review
    product_category: str # e.g. "Fast Food", "Restaurant"

class TaskAResponse(BaseModel):
    stars: int
    review_text: str
    user_style_summary: str  # e.g. "User writes in pidgin, avg 2.3 stars"

class TaskBRequest(BaseModel):
    user_id: str          # selected from dropdown OR None
    persona_text: str     # free text (for cold-start)
    top_k: int = 5        # number of recommendations to return

class TaskBResponse(BaseModel):
    recommendations: list[dict]  # [{name, category, stars, reason}]
    mode: str  # "history_based" or "cold_start"

# --- Endpoints ---

@app.post("/generate-review", response_model=TaskAResponse)
async def generate_review(request: TaskARequest):
    result = await run_task_a(request)
    return result

@app.post("/recommend", response_model=TaskBResponse)
async def recommend(request: TaskBRequest):
    result = await run_task_b(request)
    return result

@app.get("/demo-users")
async def get_demo_users():
    # Returns the curated list of demo users for the dropdown
    from config import DEMO_USERS
    return DEMO_USERS

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## 6. Database Layer

### `backend/database/db.py`

```python
import sqlite3
from contextlib import contextmanager

DB_PATH = "../data/yelp_reviews.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_user_reviews(user_id: str, limit: int = 15) -> list[dict]:
    """Fetch the most recent reviews for a user"""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT r.stars, r.text, r.date, b.name as business_name, b.categories
            FROM reviews r
            JOIN businesses b ON r.business_id = b.business_id
            WHERE r.user_id = ?
            ORDER BY r.date DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
    return [dict(row) for row in rows]

def get_user_profile(user_id: str) -> dict:
    """Get user's aggregate stats"""
    with get_db() as conn:
        row = conn.execute("""
            SELECT u.*, 
                   AVG(r.stars) as computed_avg,
                   COUNT(r.review_id) as total_reviews
            FROM users u
            LEFT JOIN reviews r ON u.user_id = r.user_id
            WHERE u.user_id = ?
            GROUP BY u.user_id
        """, (user_id,)).fetchone()
    return dict(row) if row else {}

def get_business_info(business_name: str) -> dict:
    """Find a business by name (fuzzy search)"""
    with get_db() as conn:
        row = conn.execute("""
            SELECT * FROM businesses
            WHERE name LIKE ?
            LIMIT 1
        """, (f"%{business_name}%",)).fetchone()
    return dict(row) if row else {}

def get_businesses_not_reviewed_by_user(user_id: str, category: str = None, limit: int = 50) -> list[dict]:
    """Get businesses the user has NOT reviewed yet — for Task B candidates"""
    query = """
        SELECT b.* FROM businesses b
        WHERE b.business_id NOT IN (
            SELECT business_id FROM reviews WHERE user_id = ?
        )
    """
    params = [user_id]
    if category:
        query += " AND b.categories LIKE ?"
        params.append(f"%{category}%")
    query += " ORDER BY b.stars DESC LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]
```

---

## 7. Tools

These are the functions the LangChain agent can call. Each tool is a Python function decorated with `@tool`.

### `backend/tools/user_tools.py`

```python
from langchain.tools import tool
from database.db import get_user_reviews, get_user_profile

@tool
def fetch_user_reviews(user_id: str) -> str:
    """
    Fetch the past reviews written by this user from the database.
    Returns their review history including stars, text, and business names.
    Use this to understand the user's preferences, writing style, and rating behaviour.
    """
    reviews = get_user_reviews(user_id, limit=15)
    if not reviews:
        return f"No reviews found for user {user_id}"
    
    formatted = []
    for r in reviews:
        formatted.append(
            f"- {r['business_name']} ({r['categories']}): {r['stars']} stars\n  \"{r['text'][:200]}...\""
        )
    return "\n".join(formatted)

@tool
def analyze_user_style(user_id: str) -> str:
    """
    Analyze a user's reviewing patterns: average rating, tone, topics they care about,
    language style (formal, casual, Pidgin), and what they praise or complain about most.
    Use this AFTER fetching reviews to build a user persona summary.
    """
    profile = get_user_profile(user_id)
    reviews = get_user_reviews(user_id, limit=15)
    
    avg_stars = profile.get("computed_avg", 3.0)
    review_count = profile.get("total_reviews", 0)
    
    # Build simple style summary to pass to LLM
    style_summary = f"""
    User Stats:
    - Average rating: {avg_stars:.1f} stars
    - Total reviews written: {review_count}
    - Recent reviews sample: {len(reviews)} reviews fetched
    
    Use the fetched reviews to determine:
    1. Writing style (formal/casual/Pidgin English)
    2. What they care about (price, service, food quality, ambience, speed)
    3. Emotional tone (harsh, neutral, enthusiastic)
    4. Typical review length (short sentence vs long paragraph)
    """
    return style_summary
```

### `backend/tools/business_tools.py`

```python
from langchain.tools import tool
from database.db import get_business_info, get_businesses_not_reviewed_by_user

@tool
def fetch_business_info(business_name: str) -> str:
    """
    Look up a business or product by name in the database.
    Returns the category, location, average star rating, and review count.
    Use this to understand what the product/place is known for before generating a review.
    """
    info = get_business_info(business_name)
    if not info:
        return f"Business '{business_name}' not found. Use general knowledge about this type of place."
    
    return f"""
    Business: {info['name']}
    Category: {info['categories']}
    Location: {info['city']}, {info['state']}
    Overall Rating: {info['stars']} stars ({info['review_count']} reviews)
    """

@tool
def get_candidate_businesses(user_id: str, preferred_category: str = "") -> str:
    """
    Get a list of businesses the user has NOT reviewed yet, filtered by category.
    Returns up to 20 candidate businesses for recommendation.
    Use this as input for ranking and recommendation.
    """
    candidates = get_businesses_not_reviewed_by_user(user_id, preferred_category, limit=20)
    if not candidates:
        return "No unreviewed businesses found for this user."
    
    formatted = []
    for b in candidates:
        formatted.append(f"- {b['name']} | {b['categories']} | {b['stars']} stars | {b['city']}")
    return "\n".join(formatted)
```

### `backend/tools/recommendation_tools.py`

```python
from langchain.tools import tool
from embeddings.vector_store import search_similar_businesses

@tool
def vector_search_businesses(query: str, top_k: int = 10) -> str:
    """
    ONLY USE THIS FOR COLD-START USERS (no user_id, free text persona only).
    Search for businesses semantically similar to a query description using vector embeddings.
    Example query: "cheap fast food with good service in a busy area"
    For existing users with history, use get_candidate_businesses (SQL) instead — it is faster and more accurate.
    Returns a ranked list of matching businesses.
    """
    results = search_similar_businesses(query, top_k=top_k)
    if not results:
        return "No matching businesses found."
    
    formatted = []
    for r in results:
        formatted.append(f"- {r['name']} | {r['categories']} | {r['stars']} stars | Score: {r['similarity']:.2f}")
    return "\n".join(formatted)

@tool
def rank_and_explain(user_preferences: str, candidates: str) -> str:
    """
    Final reasoning step. Given a summary of user preferences and a list of candidate businesses,
    rank the candidates from most to least suitable and explain why each fits.
    Use this AFTER either get_candidate_businesses (existing user) or vector_search_businesses (cold-start).
    Input user_preferences as a text summary. Input candidates as the raw list from the previous tool.
    """
    return f"""
    Task: Rank these candidates for a user with these preferences.
    
    User Preferences:
    {user_preferences}
    
    Candidates:
    {candidates}
    
    Please rank them 1–5, give each a score out of 10, and explain in 1–2 sentences
    why it suits this user. Write in a friendly, Nigerian-aware tone.
    """
```

> **Note:** `vector_search_businesses` is only called for cold-start (free-text persona, no user_id).
> For all existing users, the agent uses `get_candidate_businesses` which is a plain SQL query.
> This keeps the two data sources completely separate and avoids any data mixing.

---

## 8. Agents

### Why LangGraph
With LangGraph you define each reasoning step as an explicit **node** in a graph, connected by **edges**. Every step is visible, traceable, and documentable — exactly what the solution paper and judges need to see. `create_agent` hides all this logic in a black box.

---

### Task A Agent — User Modeling
**File: `backend/agents/task_a_agent.py`**

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tools.user_tools import fetch_user_reviews, analyze_user_style
from tools.business_tools import fetch_business_info

# State: everything the graph carries between nodes
class TaskAState(TypedDict):
    user_id: str
    persona_text: str
    product_name: str
    product_category: str
    user_reviews: str       # filled by node 1
    user_style: str         # filled by node 2
    business_info: str      # filled by node 3
    stars: int              # filled by node 4
    review_text: str        # filled by node 4
    style_note: str         # filled by node 4

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

# Node 1: Fetch user past reviews from SQLite
def node_fetch_reviews(state: TaskAState) -> dict:
    if state["user_id"] and state["user_id"] != "cold_start":
        reviews = fetch_user_reviews.invoke({"user_id": state["user_id"]})
    else:
        reviews = f"No history. User persona: {state['persona_text']}"
    return {"user_reviews": reviews}

# Node 2: Analyze user writing style
def node_analyze_style(state: TaskAState) -> dict:
    if state["user_id"] and state["user_id"] != "cold_start":
        style = analyze_user_style.invoke({"user_id": state["user_id"]})
    else:
        style = f"Infer style from persona: {state['persona_text']}"
    return {"user_style": style}

# Node 3: Fetch target business info from SQLite
def node_fetch_business(state: TaskAState) -> dict:
    info = fetch_business_info.invoke({"business_name": state["product_name"]})
    return {"business_info": info}

# Node 4: LLM generates the simulated review
def node_generate_review(state: TaskAState) -> dict:
    prompt = f"""
You are simulating a review written by a specific user.

USER REVIEW HISTORY:
{state['user_reviews']}

USER STYLE ANALYSIS:
{state['user_style']}

TARGET BUSINESS:
{state['business_info']}
Name: {state['product_name']} | Category: {state['product_category']}

TASK: Generate the review this user would write for the target business.
- Match their typical star rating behaviour
- Use their exact tone and language (Pidgin if they write that way)
- Mention what they usually care about (price, service, food quality, speed)
- Keep length similar to their usual reviews
- Add Nigerian context naturally (Naira, Lagos/Abuja, local food terms)
- Natural Pidgin where appropriate: "e be like say", "correct", "sharp sharp"

Respond in EXACTLY this format:
STARS: [1-5]
REVIEW: [the full review text]
STYLE_NOTE: [one sentence describing the user style you captured]
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content
    stars, review, style_note = 3, "", ""
    for line in text.strip().split("\n"):
        if line.startswith("STARS:"):
            try: stars = int(line.replace("STARS:", "").strip())
            except: stars = 3
        elif line.startswith("REVIEW:"):
            review = line.replace("REVIEW:", "").strip()
        elif line.startswith("STYLE_NOTE:"):
            style_note = line.replace("STYLE_NOTE:", "").strip()
    return {"stars": stars, "review_text": review, "style_note": style_note}

# Build the graph
def build_task_a_graph():
    graph = StateGraph(TaskAState)
    graph.add_node("fetch_reviews",   node_fetch_reviews)
    graph.add_node("analyze_style",   node_analyze_style)
    graph.add_node("fetch_business",  node_fetch_business)
    graph.add_node("generate_review", node_generate_review)
    graph.add_edge(START,             "fetch_reviews")
    graph.add_edge("fetch_reviews",   "analyze_style")
    graph.add_edge("analyze_style",   "fetch_business")
    graph.add_edge("fetch_business",  "generate_review")
    graph.add_edge("generate_review", END)
    return graph.compile()

task_a_graph = build_task_a_graph()

async def run_task_a(request) -> dict:
    result = task_a_graph.invoke({
        "user_id": request.user_id, "persona_text": request.persona_text,
        "product_name": request.product_name, "product_category": request.product_category,
        "user_reviews": "", "user_style": "", "business_info": "",
        "stars": 3, "review_text": "", "style_note": ""
    })
    return {
        "stars": result["stars"],
        "review_text": result["review_text"],
        "user_style_summary": result["style_note"]
    }
```

**Task A graph — put this diagram in your solution paper:**
```
START → [fetch_reviews] → [analyze_style] → [fetch_business] → [generate_review] → END
           (SQL)               (SQL)               (SQL)              (LLM)
```

### Task B Agent — Recommendation
**File: `backend/agents/task_b_agent.py`**

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from tools.user_tools import fetch_user_reviews, analyze_user_style
from tools.business_tools import get_candidate_businesses
from tools.recommendation_tools import vector_search_businesses

# State: everything the graph carries between nodes
class TaskBState(TypedDict):
    user_id: str
    persona_text: str
    top_k: int
    mode: str                  # "history_based" or "cold_start"
    user_reviews: str          # filled by node 1 (history mode only)
    user_style: str            # filled by node 2 (history mode only)
    candidates: str            # filled by node 3 (SQL or FAISS)
    recommendations: list[dict] # filled by node 4

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5)

# Node 1: Detect mode — history or cold start
def node_detect_mode(state: TaskBState) -> dict:
    mode = "cold_start" if state["user_id"] == "cold_start" else "history_based"
    return {"mode": mode}

# Conditional edge: route based on mode
def route_by_mode(state: TaskBState) -> Literal["fetch_history", "cold_start_search"]:
    return "fetch_history" if state["mode"] == "history_based" else "cold_start_search"

# Node 2a: History mode — fetch reviews and analyze style (SQL)
def node_fetch_history(state: TaskBState) -> dict:
    reviews = fetch_user_reviews.invoke({"user_id": state["user_id"]})
    style   = analyze_user_style.invoke({"user_id": state["user_id"]})
    return {"user_reviews": reviews, "user_style": style}

# Node 2b: Cold start — vector search via FAISS
def node_cold_start_search(state: TaskBState) -> dict:
    results = vector_search_businesses.invoke({"query": state["persona_text"], "top_k": 20})
    return {"candidates": results, "user_reviews": "", "user_style": ""}

# Node 3: History mode — get unvisited businesses from SQLite
def node_get_candidates(state: TaskBState) -> dict:
    candidates = get_candidate_businesses.invoke({
        "user_id": state["user_id"],
        "preferred_category": ""
    })
    return {"candidates": candidates}

# Node 4: LLM ranks and explains recommendations
def node_rank_recommend(state: TaskBState) -> dict:
    persona_context = state["user_style"] if state["mode"] == "history_based" else state["persona_text"]

    prompt = f"""
You are a recommendation agent. Rank and recommend the best places for this user.

USER CONTEXT:
Mode: {state['mode']}
{"Review history analysis: " + state['user_reviews'] if state['user_reviews'] else ""}
Preferences / Persona: {persona_context}

CANDIDATE PLACES:
{state['candidates']}

TASK: Pick the top {state['top_k']} best matches. For each:
- Explain in 1-2 sentences why it fits this user specifically
- Use warm, friendly Nigerian tone
- Mention value-for-money where relevant

Respond in EXACTLY this format:
1. [Place Name] | [Category] | [Reason]
2. [Place Name] | [Category] | [Reason]
...
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    text = response.content

    recommendations = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line and line[0].isdigit() and "|" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                name     = parts[0].split(".", 1)[-1].strip()
                category = parts[1].strip()
                reason   = parts[2].strip()
                recommendations.append({"name": name, "category": category, "reason": reason})
    return {"recommendations": recommendations}

# Build the graph with conditional branching
def build_task_b_graph():
    graph = StateGraph(TaskBState)

    graph.add_node("detect_mode",       node_detect_mode)
    graph.add_node("fetch_history",     node_fetch_history)
    graph.add_node("cold_start_search", node_cold_start_search)
    graph.add_node("get_candidates",    node_get_candidates)
    graph.add_node("rank_recommend",    node_rank_recommend)

    graph.add_edge(START, "detect_mode")

    # Conditional branch: history vs cold start
    graph.add_conditional_edges("detect_mode", route_by_mode, {
        "fetch_history":     "fetch_history",
        "cold_start_search": "cold_start_search"
    })

    # History path continues to SQL candidate fetch
    graph.add_edge("fetch_history",     "get_candidates")
    graph.add_edge("get_candidates",    "rank_recommend")

    # Cold start path goes straight to ranking
    graph.add_edge("cold_start_search", "rank_recommend")

    graph.add_edge("rank_recommend", END)
    return graph.compile()

task_b_graph = build_task_b_graph()

async def run_task_b(request) -> dict:
    result = task_b_graph.invoke({
        "user_id": request.user_id,
        "persona_text": request.persona_text,
        "top_k": request.top_k,
        "mode": "", "user_reviews": "", "user_style": "",
        "candidates": "", "recommendations": []
    })
    return {
        "recommendations": result["recommendations"],
        "mode": result["mode"]
    }
```

**Task B graph — put this diagram in your solution paper:**
```
START
  ↓
[detect_mode]
  ↓
  ├── history_based → [fetch_history] → [get_candidates] → [rank_recommend] → END
  │                      (SQL)               (SQL)               (LLM)
  │
  └── cold_start   → [cold_start_search]               → [rank_recommend] → END
                           (FAISS)                              (LLM)
```

---

## 9. Middleware — Nigerian Localization

Since LangGraph nodes call the LLM directly, Nigerian localization is handled as a simple helper function you call inside any node before the LLM call. No special middleware class needed.

**File: `backend/middleware/nigerian_localization.py`**

```python
NIGERIAN_ADDENDUM = """
NIGERIAN LOCALIZATION RULES:
- Use Naija Pidgin naturally where the user's style calls for it
- Reference Nigerian price awareness (value for Naira)
- Use local food terms: jollof, suya, puff puff, egusi, buka, mama put
- Reference Nigerian cities: Lagos, Abuja, Port Harcourt, Ikeja, VI, Lekki
- Pidgin phrases: "e don do", "no be small thing", "correct", "sharp sharp",
  "e be like say", "dem no try", "e dey", "wetin"
- Only use Pidgin if the user's history suggests they write that way
- Never force Pidgin on a user who writes formal English
"""

def inject_nigerian_context(base_prompt: str) -> str:
    """Call this inside any node prompt to add Nigerian localization"""
    return base_prompt + "\n\n" + NIGERIAN_ADDENDUM
```

Usage inside any node:
```python
from middleware.nigerian_localization import inject_nigerian_context

prompt = inject_nigerian_context(f"""
You are simulating a review...
{state['user_reviews']}
...
""")
response = llm.invoke([HumanMessage(content=prompt)])
```

---

## 10. Vector Store (for Task B cold-start)

**File: `backend/embeddings/vector_store.py`**

```python
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_PATH = "../data/faiss_index/businesses.index"
META_PATH = "../data/faiss_index/businesses_meta.pkl"

embedder = SentenceTransformer(MODEL_NAME)

def build_index(businesses: list[dict]):
    """Build FAISS index from businesses list. Run once at setup."""
    texts = [f"{b['name']} {b['categories']} {b['city']}" for b in businesses]
    embeddings = embedder.encode(texts, show_progress_bar=True)
    
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))
    
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(businesses, f)
    
    print(f"Built FAISS index with {len(businesses)} businesses")

def search_similar_businesses(query: str, top_k: int = 10) -> list[dict]:
    """Search FAISS index for businesses matching the query"""
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        businesses = pickle.load(f)
    
    query_embedding = embedder.encode([query]).astype("float32")
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(businesses):
            biz = businesses[idx].copy()
            biz["similarity"] = float(1 / (1 + dist))  # Convert distance to similarity score
            results.append(biz)
    
    return results
```

---

## 11. Frontend — Custom UI (HTML/CSS/JS or React)

The frontend is a custom-built UI — design and style it however you want. It communicates with the FastAPI backend via HTTP fetch calls. No Streamlit, no Python in the frontend.

### What the Frontend Must Do

**Overall layout:**
- Single page with two tabs: "Simulate a Review" (Task A) and "Get Recommendations" (Task B)
- On load, fetch the demo users list from `GET /demo-users` and populate the dropdowns

---

### Task A Tab — Simulate a Review

**Inputs:**
- Dropdown: select a demo user (populated from `/demo-users`)
- OR toggle to "Cold Start" mode → show a textarea for free-text persona description
- Text input: place/product name (e.g. "KFC Lekki")
- Dropdown: category (Restaurant, Fast Food, Bar, Cafe, Hotel, Supermarket, Other)
- Submit button: "Generate Review"

**On submit — call:**
```
POST /generate-review
Content-Type: application/json

{
  "user_id": "abc123",         // from dropdown, or "cold_start"
  "persona_text": "",          // only filled if cold_start mode
  "product_name": "KFC Lekki",
  "product_category": "Fast Food"
}
```

**Display output:**
- Star rating (1–5) displayed visually as filled/empty stars
- The generated review text in a styled card
- The style note below (e.g. "User writes in Pidgin, avg 2.3 stars")
- Show a loading spinner while waiting for the API response

---

### Task B Tab — Get Recommendations

**Inputs:**
- Dropdown: select a demo user (populated from `/demo-users`)
- OR toggle to "Cold Start" mode → show a textarea for free-text persona description
- Number input or slider: how many recommendations (3–10, default 5)
- Submit button: "Get Recommendations"

**On submit — call:**
```
POST /recommend
Content-Type: application/json

{
  "user_id": "abc123",         // from dropdown, or "cold_start"
  "persona_text": "",          // only filled if cold_start mode
  "top_k": 5
}
```

**Display output:**
- A badge showing the mode: "Based on review history" or "Cold-start"
- A ranked list of recommendation cards, each showing:
  - Place name
  - Category
  - Reason it was recommended
- Show a loading spinner while waiting

---

### API Base URL

```javascript
// In development (local)
const API_URL = "http://localhost:8000"

// In Docker (frontend container talking to backend container)
const API_URL = "http://backend:8000"

// In production (both served from same domain or set via env)
const API_URL = window.ENV_API_URL || "http://localhost:8000"
```

---

### Frontend Dockerfile

```dockerfile
FROM nginx:alpine
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

If using React, replace with:

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```
```

---

## 12. Docker Setup

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

---

## 13. Requirements

### `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn==0.30.0
pydantic==2.7.0
langgraph==0.2.0
langchain==0.2.0
langchain-core==0.2.0
langchain-groq==0.1.0
langchain-openai==0.1.0
sentence-transformers==3.0.0
faiss-cpu==1.8.0
numpy==1.26.0
python-dotenv==1.0.0
httpx==0.27.0
```

### Frontend dependencies
If using plain HTML/CSS/JS — no package manager needed, just files.

If using React:
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
```

---

## 14. Environment Variables

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_key_here_optional
```

Get a free Groq API key at: **https://console.groq.com**

---

## 15. Setup Script (Run Once)

**File: `scripts/setup_data.py`**

```python
"""
Run this ONCE before starting the app.
It loads the Yelp JSON files into SQLite and builds the FAISS index.

Usage:
    python scripts/setup_data.py \
        --reviews path/to/yelp_academic_dataset_review.json \
        --businesses path/to/yelp_academic_dataset_business.json \
        --users path/to/yelp_academic_dataset_user.json
"""

import json
import sqlite3
import argparse
import sys
sys.path.append("./backend")

from embeddings.vector_store import build_index

def load_reviews(path, conn, limit=500_000):
    print(f"Loading reviews (up to {limit})...")
    cursor = conn.cursor()
    count = 0
    with open(path, "r") as f:
        for line in f:
            if count >= limit:
                break
            r = json.loads(line)
            cursor.execute(
                "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?,?)",
                (r["review_id"], r["user_id"], r["business_id"], r["stars"], r["text"], r["date"])
            )
            count += 1
    conn.commit()
    print(f"Loaded {count} reviews")

def load_businesses(path, conn, limit=150_000):
    print(f"Loading businesses (up to {limit})...")
    cursor = conn.cursor()
    businesses = []
    count = 0
    with open(path, "r") as f:
        for line in f:
            if count >= limit:
                break
            b = json.loads(line)
            categories = b.get("categories") or ""
            cursor.execute(
                "INSERT OR IGNORE INTO businesses VALUES (?,?,?,?,?,?,?)",
                (b["business_id"], b["name"], categories, b["city"], b["state"], b["stars"], b["review_count"])
            )
            businesses.append({"business_id": b["business_id"], "name": b["name"],
                               "categories": categories, "city": b["city"], "stars": b["stars"]})
            count += 1
    conn.commit()
    print(f"Loaded {count} businesses")
    return businesses

def load_users(path, conn, limit=100_000):
    print(f"Loading users (up to {limit})...")
    cursor = conn.cursor()
    count = 0
    with open(path, "r") as f:
        for line in f:
            if count >= limit:
                break
            u = json.loads(line)
            cursor.execute(
                "INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
                (u["user_id"], u["name"], u["review_count"], u["average_stars"], u["name"])
            )
            count += 1
    conn.commit()
    print(f"Loaded {count} users")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--businesses", required=True)
    parser.add_argument("--users", required=True)
    args = parser.parse_args()

    conn = sqlite3.connect("./data/yelp_reviews.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, name TEXT, review_count INTEGER,
        average_stars REAL, display_name TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS businesses (
        business_id TEXT PRIMARY KEY, name TEXT, categories TEXT,
        city TEXT, state TEXT, stars REAL, review_count INTEGER)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reviews (
        review_id TEXT PRIMARY KEY, user_id TEXT, business_id TEXT,
        stars INTEGER, text TEXT, date TEXT)""")
    conn.commit()

    businesses = load_businesses(args.businesses, conn)
    load_users(args.users, conn)
    load_reviews(args.reviews, conn)
    conn.close()

    print("Building FAISS vector index...")
    build_index(businesses)

    print("\n✅ Setup complete! You can now run the app.")

if __name__ == "__main__":
    main()
```

---

## 16. Evaluation Metrics

The judges will evaluate using these metrics. Make sure your code outputs them:

### Task A
| Metric | What it measures | How to score well |
|---|---|---|
| ROUGE / BERTScore | How similar generated review is to real reviews | Match user's vocabulary and topics |
| RMSE | How accurate the predicted star rating is | Base rating on user's avg + product signals |
| Behavioural Fidelity | Does it sound like that user? (human eval) | Capture writing style, tone, Pidgin level |

### Task B
| Metric | Points | How to score well |
|---|---|---|
| NDCG@10 / Hit Rate | 30 | Return actually good recommendations in top 10 |
| Cold-Start & Cross-Domain | 25 | Free text persona input path must work well |
| Contextual Relevance | 20 | Recommendations must make sense for the user |
| Solution Paper | 15 | Write a clear, detailed 4–8 page paper |
| Code Reproducibility | 10 | Clean README, works first try |

---

## 17. Nigerian Localization (Bonus Marks)

Add this to EVERY system prompt to score bonus marks:

```
NIGERIAN CONTEXT RULES:
- Use Naija Pidgin naturally where the user's style calls for it
- Reference Nigerian price awareness ("value for Naira")
- Use local food terms: jollof, suya, puff puff, egusi, buka, mama put
- Reference Nigerian cities: Lagos, Abuja, Port Harcourt, Ikeja, VI, Lekki
- Common Pidgin phrases: "e don do", "no be small thing", "correct", "sharp sharp",
  "e be like say", "dem no try", "e dey", "wetin"
- Only use Pidgin if the user's history suggests they write that way
- Never force Pidgin on a user who writes formal English
```

---

## 18. Deployment (Hugging Face Spaces)

1. Create a new Space at **huggingface.co/spaces**
2. Select **Docker** as the SDK
3. Push your repo with the `docker-compose.yml`
4. Set secrets: `GROQ_API_KEY` in Space settings
5. The app will be live at `https://huggingface.co/spaces/YOUR_USERNAME/bct-hackathon`

Submit this URL as your "Link to Agent Built" in the submission form.

---

## 19. Submission Checklist

- [ ] Task A agent generates star ratings + reviews that match user style
- [ ] Task B agent returns ranked recommendations with explanations
- [ ] Frontend has two tabs — one per task
- [ ] Task B supports both dropdown (existing user) and free text (cold-start)
- [ ] Nigerian localization middleware is applied
- [ ] App is containerized with Docker
- [ ] App is deployed and accessible via a public URL
- [ ] GitHub repo is clean with a clear README
- [ ] Solution paper is 4–8 pages covering architecture, experiments, ablation studies
- [ ] All three deliverables submitted before May 24, midnight

---

*Good luck! Focus on the solution paper — judges read it first.*
