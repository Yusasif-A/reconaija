# Architecture Improvements for BCT Hackathon

## Overview
This document outlines the enhanced LangGraph agent architecture with self-reflection, cross-domain expansion, and validation nodes added to maximize rubric scores.

---

## Task A Agent - User Modeling with Reflection

### Enhanced Flow
```
START → fetch_reviews → analyze_style → fetch_business 
      → generate_review → reflect_and_improve → END
```

### New Node: `reflect_and_improve`

**Purpose**: Self-checks generated reviews for consistency with user style before returning

**Key Features**:
- Compares generated star rating with user's average
- Detects inconsistencies (e.g., harsh critic giving 5 stars)
- LLM reflects on its own output and corrects if needed
- Only rewrites if star difference > 1.5 from user average
- Adds reflection note to output

**Rubric Impact**:
- Demonstrates advanced reasoning (self-correction)
- Improves output quality and authenticity
- Shows understanding of user modeling beyond simple generation

**Implementation**:
```python
def node_reflect_and_improve(state: TaskAState) -> dict:
    """Self-check the generated review for consistency"""
    user_avg = extract_avg_from_style(state["user_style"])
    star_diff = abs(state["stars"] - user_avg)
    
    if star_diff > 1.5:
        # Ask LLM to reflect and correct
        corrected = llm_reflect(state)
        return corrected
    
    return {"needs_reflection": False}  # Review is consistent
```

---

## Task B Agent - Recommendations with Cross-Domain & Validation

### Enhanced Flow
```
START → detect_mode
  ├── history path → fetch_history → expand_domain 
  │                → get_candidates → rank_recommend 
  │                → validate_recommendations → END
  └── cold start path → cold_start_search 
                     → rank_recommend 
                     → validate_recommendations → END
```

### New Node 1: `expand_domain` (Worth 25 Points)

**Purpose**: Implements cross-domain recommendation handling per rubric requirement

**Key Features**:
- Analyzes user's review history to find primary category
- Maps primary category to 2 adjacent categories
- Expands candidate search to include related domains
- Prevents all recommendations from being the same type

**Example**:
- User mostly reviews "Fast Food" → expands to "Casual Dining" + "Street Food"
- User mostly reviews "Bars" → expands to "Nightlife" + "Lounges"

**Rubric Impact**:
- Directly addresses "Cross-Domain Handling" (25 points)
- Shows understanding of recommendation diversity
- Improves user experience with varied suggestions

**Implementation**:
```python
def node_expand_domain(state: TaskBState) -> dict:
    """Identify primary category and add adjacent ones"""
    primary_cat = get_user_primary_category(state["user_id"])
    
    category_neighbors = {
        "Fast Food": ["Casual Dining", "Street Food"],
        "Bars": ["Nightlife", "Lounges"],
        "Restaurants": ["Cafes", "Food Trucks"],
        # ... more mappings
    }
    
    extra_cats = category_neighbors.get(primary_cat, ["Casual Dining"])
    
    return {
        "primary_category": primary_cat,
        "extra_categories": extra_cats
    }
```

### New Node 2: `validate_recommendations`

**Purpose**: Final quality check before returning recommendations

**Key Features**:
1. **Removes already-reviewed businesses**
   - Checks user's review history
   - Filters out places they've already visited
   - Prevents embarrassing duplicate recommendations

2. **Ensures category diversity**
   - Checks if >70% of recommendations are same category
   - Swaps one for a different category if too homogeneous
   - Improves recommendation variety

**Rubric Impact**:
- Shows attention to recommendation quality
- Demonstrates understanding of user experience
- Prevents obvious mistakes (recommending visited places)

**Implementation**:
```python
def node_validate_recommendations(state: TaskBState) -> dict:
    """Validate quality before returning"""
    recommendations = state["recommendations"]
    reviewed_names = state["reviewed_businesses"]
    
    # Step 1: Remove already-reviewed
    filtered = [r for r in recommendations 
                if r["name"] not in reviewed_names]
    
    # Step 2: Check category diversity
    categories = [r["category"] for r in filtered]
    if most_common_category_percentage > 0.7:
        # Swap one for diversity
        swap_for_different_category(filtered)
    
    return {"recommendations": filtered}
```

---

## Nigerian Localization Enhancement

### Already Implemented: `inject_nigerian_context()`

**Purpose**: Adds Nigerian cultural context to every LLM prompt

**Key Features**:
- Appends Nigerian localization rules to prompts
- Ensures Pidgin English usage when appropriate
- Adds budget consciousness and Gen Z tone detection
- References Nigerian food culture (jollof, suya, buka)
- Mentions Naira and Lagos/Abuja context

**Usage**:
Called in both `node_generate_review` (Task A) and `node_rank_recommend` (Task B) before every LLM invocation.

**Rubric Impact**:
- Demonstrates cultural localization
- Shows understanding of target audience
- Makes reviews authentic and relatable

---

## Summary of Improvements

### Task A (User Modeling)
| Feature | Purpose | Rubric Impact |
|---------|---------|---------------|
| Reflection Node | Self-checks review consistency | Advanced reasoning, quality control |
| Nigerian Context Injection | Authentic local voice | Cultural localization |

### Task B (Recommendations)
| Feature | Purpose | Rubric Impact |
|---------|---------|---------------|
| Cross-Domain Expansion | Recommend across categories | **25 points** cross-domain handling |
| Validation Node | Remove duplicates, ensure diversity | Quality control, user experience |
| Nigerian Context Injection | Local-friendly explanations | Cultural localization |

---

## Total Architecture

### Tools Count: 11 Tools
1. `fetch_user_reviews` - Get review history
2. `analyze_user_style` - Analyze writing patterns
3. `fetch_business_info` - Get business details
4. `get_candidate_businesses` - SQL candidate search
5. `vector_search_businesses` - ChromaDB semantic search
6. `extract_personality_traits` - Advanced analysis
7. `detect_review_tone` - Tone detection
8. `predict_rating_tendency` - Rating prediction
9. `analyze_review_topics` - Topic extraction
10. `generate_user_summary` - User summarization
11. `get_user_primary_category` - Category analysis

### Node Count: 12 Nodes
**Task A**: 5 nodes
- fetch_reviews
- analyze_style
- fetch_business
- generate_review
- **reflect_and_improve** ✨

**Task B**: 7 nodes
- detect_mode
- fetch_history
- **expand_domain** ✨ (worth 25 points)
- cold_start_search
- get_candidates
- rank_recommend
- **validate_recommendations** ✨

### Key Differentiators
1. ✅ Self-reflection and correction (Task A)
2. ✅ Cross-domain recommendation expansion (Task B) - **25 points**
3. ✅ Quality validation before output (Task B)
4. ✅ Nigerian cultural localization throughout
5. ✅ Conditional branching (history vs cold-start)
6. ✅ 11 specialized tools
7. ✅ ChromaDB semantic search
8. ✅ MySQL relational queries

---

## How This Wins

1. **Advanced Architecture**: More nodes than basic implementations
2. **Self-Improvement**: Reflection node shows meta-reasoning
3. **Cross-Domain**: Directly addresses 25-point rubric requirement
4. **Quality Control**: Validation prevents obvious mistakes
5. **Cultural Authenticity**: Nigerian context injection throughout
6. **Tool Diversity**: 11 tools show comprehensive system design
7. **Dual Pathways**: Handles both history-based and cold-start scenarios

This architecture demonstrates understanding of:
- Multi-agent systems
- Self-correction and reflection
- Cross-domain recommendation strategies
- Quality assurance in AI systems
- Cultural localization
- Production-ready error handling
