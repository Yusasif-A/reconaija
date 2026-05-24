# RecoNaija 🇳🇬 - Nigerian Yelp Review Agent

> BCT Hackathon 2026 Submission - LLM Agent for Nigerian Restaurant Reviews & Recommendations

RecoNaija is an intelligent agent system that simulates how Nigerians review restaurants and provides personalized recommendations. Built with LangGraph, it incorporates Nigerian cultural context, Pidgin English, and Gen Z vibes.

## 🌟 Features

### Task A: Review Simulation
- Analyzes user's past review history
- Extracts personality traits, tone, and rating patterns
- Generates authentic reviews matching user's style
- Incorporates Nigerian cultural elements (Pidgin, food terms, Naira mentions)
- Detects and matches Gen Z slang usage

### Task B: Smart Recommendations
- **History-based**: Uses SQL queries for users with review history
- **Cold-start**: Uses ChromaDB vector search for new users with free-text personas
- Nigerian-friendly explanations with local context
- Considers affordability, food quality, and vibes

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │  ← Tailwind CSS, Nigerian-themed UI
│  (Vite + React) │
└────────┬────────┘
         │ HTTP/JSON
         ▼
┌─────────────────┐
│  FastAPI Backend│  ← LangGraph Agents
│  + LangGraph    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌──────────┐
│ MySQL │  │ ChromaDB │  ← nomic-embedding
│  DB   │  │ Vectors  │
└───────┘  └──────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI + Python 3.11 |
| Agent Framework | LangGraph (StateGraph) |
| LLM | Gemma-4-E4B-it (via PublicAI) |
| Embeddings | nomic-embedding (via PublicAI) |
| Database | MySQL |
| Vector Store | ChromaDB |
| Containerization | Docker + Docker Compose |

## 📦 Project Structure

```
dsc-hackathon/
├── backend/
│   ├── agents/
│   │   ├── task_a_agent.py      # User modeling (4-node graph)
│   │   └── task_b_agent.py      # Recommendations (conditional branching)
│   ├── tools/
│   │   ├── user_tools.py        # User data fetching
│   │   ├── business_tools.py    # Business queries
│   │   ├── recommendation_tools.py  # Vector search & ranking
│   │   └── advanced_analysis_tools.py  # 5 specialized analysis tools
│   ├── middleware/
│   │   └── nigerian_localization.py  # Nigerian context injection
│   ├── database/
│   │   └── db.py                # MySQL queries
│   ├── embeddings/
│   │   └── vector_store.py      # FAISS index builder/searcher
│   ├── config.py                # LLM & DB configuration
│   ├── main.py                  # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TaskA.jsx        # Review generation UI
│   │   │   ├── TaskB.jsx        # Recommendations UI
│   │   │   ├── UserDropdown.jsx
│   │   │   ├── StarRating.jsx
│   │   │   └── ReviewCard.jsx
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── main.jsx
│   ├── package.json
│   └── tailwind.config.js
├── scripts/
│   ├── load_yelp_to_mysql.py    # Data loading script
│   └── build_faiss_index.py     # FAISS index builder
├── data/
│   └── faiss_index/             # Vector index storage
├── docker-compose.yml
└── .env
```

## 🚀 Quick Start with Docker

### Running with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/Yusasif-A/reconaija.git
   cd reconaija
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

That's it! Docker will handle all dependencies, database setup, and service orchestration.

---

## 🛠️ Manual Setup (Alternative)

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL database
- Yelp dataset (downloaded)

### 1. Clone and Setup Environment

```bash
cd dsc-hackathon

# Create .env file
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 2. Load Data into MySQL

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Load Yelp data (50k reviews, 20k businesses, 20k users)
cd ..
python scripts/load_yelp_to_mysql.py
```

This creates:
- Database: `RecoNaija`
- 8 Nigerian-themed demo users (Lagos Foodie, Budget King, Pidgin Pro, etc.)

### 3. Build ChromaDB Vector Store

```bash
python scripts/build_faiss_index.py
```

### 4. Start Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

### 6. Docker (Optional)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## 🎯 Usage

### Task A: Generate Review

1. Select a demo user (e.g., "The Pidgin Pro") or enable cold-start
2. Enter restaurant name (e.g., "Chicken Republic Lekki")
3. Select category
4. Click "Generate Review"
5. See authentic Nigerian-style review matching user's personality

### Task B: Get Recommendations

1. Select a demo user or describe your persona
2. Choose number of recommendations (3-10)
3. Click "Get Recommendations"
4. See ranked recommendations with Nigerian-friendly explanations

## 🇳🇬 Nigerian Context Features

- **Pidgin English**: "e don do", "no be small thing", "sharp sharp", "correct"
- **Food Terms**: jollof rice, suya, puff puff, buka, mama put
- **Cities**: Lagos (Lekki, VI, Ikeja), Abuja, Port Harcourt
- **Currency**: Naira (₦) mentions for affordability
- **Gen Z Slang**: "lowkey", "vibes", "hits different", "no cap"
- **Cultural Refs**: Shoprite, Chicken Republic, local food spots

## 🧠 Agent Architecture

### Task A Agent (LangGraph StateGraph)

```
START → [fetch_reviews] → [analyze_style] → [fetch_business] → [generate_review] → END
           (SQL)              (Analysis)          (SQL)              (LLM+Nigerian)
```

**Nodes:**
1. `fetch_reviews`: Get user's past reviews from MySQL
2. `analyze_style`: Extract personality, tone, Pidgin level, budget consciousness
3. `fetch_business`: Get target restaurant info
4. `generate_review`: LLM generates review with Nigerian context

### Task B Agent (Conditional Branching)

```
START
  ↓
[detect_mode]
  ↓
  ├── history_based → [fetch_history] → [get_candidates] → [rank_recommend] → END
  │                      (SQL)              (SQL)               (LLM)
  │
  └── cold_start   → [cold_start_search]               → [rank_recommend] → END
                           (FAISS)                           (LLM)
```

## 🔧 Advanced Tools (Enhanced Architecture)

1. **extract_personality_traits** - Optimism, detail orientation, emotional expression
2. **detect_review_tone** - Formality, humor, Nigerian cultural elements
3. **predict_rating_tendency** - Rating patterns, leniency, consistency
4. **analyze_review_topics** - Focus areas (food/service/price/ambience)
5. **generate_user_summary** - Meta-tool synthesizing all insights

## 📊 API Endpoints

```
GET  /                    # API info
GET  /demo-users          # List Nigerian-themed demo users
POST /generate-review     # Task A: Generate review
POST /recommend           # Task B: Get recommendations
GET  /health              # Health check
```

## 🧪 Testing

### Test Task A
```bash
curl -X POST http://localhost:8000/generate-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id_from_demo_users>",
    "persona_text": "",
    "product_name": "Chicken Republic Lekki",
    "product_category": "Fast Food"
  }'
```

### Test Task B
```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "cold_start",
    "persona_text": "I love spicy Nigerian food and affordable places",
    "top_k": 5
  }'
```

## 🎨 Frontend Features

- Nigerian flag colors (green/white theme)
- Responsive design
- Loading states with spinners
- Error handling
- Tab-based navigation
- Cold-start toggle
- Slider for recommendation count
- Star rating visualization

## 📝 Demo Users

1. **The Lagos Foodie** - Loves upscale dining, detailed reviews
2. **The Budget King** - Value-conscious, mentions prices
3. **The Harsh Critic** - Low ratings, brutally honest
4. **The Hype Man** - Loves everything, always positive
5. **The Pidgin Pro** - Writes in Nigerian Pidgin English
6. **The Quick Reviewer** - Short, casual reviews
7. **The Service Checker** - Focuses on staff and speed
8. **The Jollof Judge** - Rates based on Nigerian food quality

## 🐳 Deployment

### Hugging Face Spaces (Docker)

1. Create new Space with Docker SDK
2. Push repository
3. Set secrets: `DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME`
4. Space will auto-deploy

### Railway

1. Create new project
2. Add MySQL database
3. Deploy backend and frontend services
4. Set environment variables

## 📄 License

MIT License - BCT Hackathon 2026

## 👥 Team

Built with ❤️ for BCT Hackathon 2026

## 🙏 Acknowledgments

- Yelp Dataset
- LangChain & LangGraph
- PublicAI for Gemma models
- Nigerian food culture 🇳🇬
