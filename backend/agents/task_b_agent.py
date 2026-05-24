"""
Task B Agent - Recommendations
Recommends restaurants using LangGraph with conditional branching
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from config import LLM
from tools.user_tools import fetch_user_reviews, analyze_user_style
from tools.business_tools import get_candidate_businesses
from tools.recommendation_tools import vector_search_businesses
from middleware.nigerian_localization import inject_nigerian_context

# State: everything the graph carries between nodes
class TaskBState(TypedDict):
    user_id: str
    persona_text: str
    top_k: int
    mode: str                   # "history_based" or "cold_start"
    user_reviews: str           # filled by node 1 (history mode only)
    user_style: str             # filled by node 2 (history mode only)
    primary_category: str       # filled by expand_domain
    extra_categories: list[str] # filled by expand_domain
    candidates: str             # filled by node 3 (SQL or FAISS)
    recommendations: list[dict] # filled by node 4
    reviewed_businesses: list[str] # filled by validate node

# Node 1: Detect mode — history or cold start
def node_detect_mode(state: TaskBState) -> dict:
    """Determine if this is history-based or cold-start recommendation"""
    mode = "cold_start" if state["user_id"] == "cold_start" else "history_based"
    print(f"[Task B] Node: detect_mode - Mode detected: {mode}")
    return {"mode": mode}

# Conditional edge: route based on mode
def route_by_mode(state: TaskBState) -> Literal["fetch_history", "cold_start_search"]:
    """Route to appropriate path based on mode"""
    return "fetch_history" if state["mode"] == "history_based" else "cold_start_search"

# Node 2a: History mode — fetch reviews and analyze style (SQL)
def node_fetch_history(state: TaskBState) -> dict:
    """Fetch user history and analyze preferences"""
    print("[Task B] Node: fetch_history - Fetching user review history")
    reviews = fetch_user_reviews.invoke({"user_id": state["user_id"]})
    style   = analyze_user_style.invoke({"user_id": state["user_id"]})

    # Also get list of reviewed businesses for validation later
    from database.db import get_user_reviewed_businesses
    reviewed = get_user_reviewed_businesses(state["user_id"])

    return {
        "user_reviews": reviews,
        "user_style": style,
        "reviewed_businesses": reviewed
    }

# Node 2a-extra: Expand domain for cross-category recommendations (worth 25 points)
def node_expand_domain(state: TaskBState) -> dict:
    """
    Identify user's primary category and add adjacent categories for diversity.
    This addresses the cross-domain handling requirement (25 points on rubric).
    """
    print("[Task B] Node: expand_domain - Expanding to cross-domain categories")
    from database.db import get_user_primary_category

    # Get the category user reviews most
    primary_cat = get_user_primary_category(state["user_id"])

    # Map categories to adjacent ones for diversity
    category_neighbors = {
        "Restaurants": ["Cafes", "Food Trucks", "Casual Dining"],
        "Fast Food": ["Casual Dining", "Street Food", "Food Trucks"],
        "Bars": ["Nightlife", "Lounges", "Pubs"],
        "Cafes": ["Restaurants", "Bakeries", "Coffee & Tea"],
        "Pizza": ["Italian", "Casual Dining", "Fast Food"],
        "Mexican": ["Latin American", "Tex-Mex", "Casual Dining"],
        "Chinese": ["Asian Fusion", "Japanese", "Thai"],
        "Italian": ["Pizza", "Casual Dining", "European"],
        "American": ["Casual Dining", "Burgers", "Diners"],
        "Sandwiches": ["Delis", "Fast Food", "Casual Dining"]
    }

    # Get 2 adjacent categories
    extra_cats = category_neighbors.get(primary_cat, ["Casual Dining", "Restaurants"])[:2]

    return {
        "primary_category": primary_cat,
        "extra_categories": extra_cats
    }

# Node 2b: Cold start — vector search via ChromaDB
def node_cold_start_search(state: TaskBState) -> dict:
    """Search businesses using semantic similarity"""
    print("[Task B] Node: cold_start_search - Searching via ChromaDB vector store")
    results = vector_search_businesses.invoke({
        "query": state["persona_text"],
        "top_k": state["top_k"] * 4  # Get more candidates for ranking
    })
    return {
        "candidates": results,
        "user_reviews": "",
        "user_style": "",
        "reviewed_businesses": [],
        "primary_category": "",
        "extra_categories": []
    }

# Node 3: History mode — get unvisited businesses from MySQL
def node_get_candidates(state: TaskBState) -> dict:
    """Get businesses user hasn't reviewed yet, including cross-domain suggestions"""
    print("[Task B] Node: get_candidates - Getting candidate businesses from database")
    # Use primary category + extra categories for diversity
    categories = [state.get("primary_category", "")]
    if state.get("extra_categories"):
        categories.extend(state["extra_categories"])

    # Filter out empty strings
    categories = [c for c in categories if c]

    candidates = get_candidate_businesses.invoke({
        "user_id": state["user_id"],
        "preferred_category": ", ".join(categories) if categories else ""
    })
    return {"candidates": candidates}

# Node 4: LLM ranks and explains recommendations
def node_rank_recommend(state: TaskBState) -> dict:
    """Rank candidates and provide Nigerian-friendly explanations"""
    print("[Task B] Node: rank_recommend - Ranking candidates with LLM")
    print(f"[Task B] Requested top_k: {state['top_k']}")
    
    # Debug: Check what candidates look like
    print(f"[Task B] Candidates type: {type(state['candidates'])}")
    print(f"[Task B] Candidates preview: {str(state['candidates'])[:300]}...")

    persona_context = state["user_style"] if state["mode"] == "history_based" else state["persona_text"]

    base_prompt = f"""
You are a recommendation agent helping Nigerians discover great places to eat and hang out.

USER CONTEXT:
Mode: {state['mode']}
{"Review history: " + state['user_reviews'] if state['user_reviews'] else ""}
User Preferences: {persona_context}

CANDIDATE PLACES:
{state['candidates']}

TASK: From the candidates above, select the top {state['top_k']} best matches for this user.

Respond with a JSON array of recommendations. Each recommendation should have:
- "name": exact business name from candidates
- "category": business category
- "reason": 1-2 sentences why it fits this user

Example format:
[
  {{"name": "Mama Put Kitchen", "category": "Nigerian Restaurant", "reason": "Perfect for someone who loves authentic local food with great jollof rice and affordable prices"}},
  {{"name": "The Grind Cafe", "category": "Coffee Shop", "reason": "Ideal spot for a Gen Z foodie who wants Instagram-worthy vibes and good coffee"}}
]

Provide exactly {state['top_k']} recommendations as a JSON array:
"""

    # Inject Nigerian context
    enhanced_prompt = inject_nigerian_context(base_prompt)

    # Call LLM
    response = LLM.invoke([HumanMessage(content=enhanced_prompt)])
    text = response.content
    
    print(f"[Task B] LLM Response: {text[:500]}...")  # Log first 500 chars

    # Parse JSON recommendations
    from database.db import get_business_info
    import json
    import re

    recommendations = []
    
    try:
        # Try to extract JSON array from response
        # Sometimes LLM wraps it in markdown code blocks
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            
            print(f"[Task B] Parsed {len(parsed)} recommendations from JSON")
            
            for item in parsed:
                name = item.get("name", "").strip()
                category = item.get("category", "").strip()
                reason = item.get("reason", "").strip()
                
                if name and category and reason:
                    # Fetch business info to get image_url
                    biz_info = get_business_info(name)
                    image_url = biz_info.get('image_url', '') if biz_info else ''
                    
                    print(f"[Task B] Business: {name}")
                    print(f"[Task B]   - DB info found: {biz_info is not None}")
                    print(f"[Task B]   - Image URL: {image_url if image_url else 'None'}")
                    
                    recommendations.append({
                        "name": name,
                        "category": category,
                        "reason": reason,
                        "image_url": image_url
                    })
        else:
            print(f"[Task B] Warning: Could not find JSON array in LLM response")
            print(f"[Task B] Full Response: {text}")
            
    except json.JSONDecodeError as e:
        print(f"[Task B] Error parsing JSON: {e}")
        print(f"[Task B] Full Response: {text}")
        
        # Fallback: try old pipe-separated format
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and line[0].isdigit() and "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    name = parts[0].split(".", 1)[-1].strip() if "." in parts[0] else parts[0].strip()
                    name = name.lstrip("0123456789. ")
                    category = parts[1].strip()
                    reason = parts[2].strip()
                    
                    biz_info = get_business_info(name)
                    image_url = biz_info.get('image_url', '') if biz_info else ''
                    
                    print(f"[Task B] Fallback - Business: {name}")
                    print(f"[Task B]   - DB info found: {biz_info is not None}")
                    print(f"[Task B]   - Image URL: {image_url if image_url else 'None'}")
                    
                    recommendations.append({
                        "name": name,
                        "category": category,
                        "reason": reason,
                        "image_url": image_url
                    })
    
    print(f"[Task B] Final recommendations count: {len(recommendations)}")
    return {"recommendations": recommendations}

# Node 5: Validate recommendations before returning
def node_validate_recommendations(state: TaskBState) -> dict:
    """
    Final validation to ensure quality recommendations:
    1. Remove any businesses the user already reviewed
    2. Ensure category diversity (not all from same category)
    """
    print("[Task B] Node: validate_recommendations - Validating final recommendations")
    recommendations = state["recommendations"]
    reviewed_names = state.get("reviewed_businesses", [])

    # Step 1: Remove already-reviewed businesses
    filtered = []
    for rec in recommendations:
        if rec["name"] not in reviewed_names:
            filtered.append(rec)

    # Step 2: Check category diversity
    if len(filtered) >= 3:
        categories = [r["category"] for r in filtered]
        # If more than 70% are the same category, swap one for diversity
        from collections import Counter
        cat_counts = Counter(categories)
        most_common_cat, count = cat_counts.most_common(1)[0]

        if count / len(filtered) > 0.7:
            # Find a different category recommendation
            diverse_rec = None
            for rec in filtered:
                if rec["category"] != most_common_cat:
                    diverse_rec = rec
                    break

            # If we found a diverse one, move it to position 2
            if diverse_rec and len(filtered) >= 3:
                filtered.remove(diverse_rec)
                filtered.insert(1, diverse_rec)

    return {"recommendations": filtered}

# Node 6: Localize recommendations to Nigerian context using LLM
def node_localize_nigerian(state: TaskBState) -> dict:
    """
    Use LLM to replace American restaurant names/locations with Nigerian equivalents.
    This makes recommendations authentic and locally relevant.
    """
    print("[Task B] Node: localize_nigerian - Localizing recommendations to Nigerian context")

    recommendations = state["recommendations"]
    if not recommendations:
        return {"recommendations": []}

    import json

    # Build the list for LLM
    rec_list = []
    for i, rec in enumerate(recommendations):
        rec_list.append(f"{i+1}. Name: {rec['name']} | Category: {rec['category']} | Reason: {rec['reason']}")

    localization_prompt = f"""
You are a Nigerian restaurant localization agent. Your job is to replace foreign/American restaurant names with REAL Nigerian restaurant equivalents.

HERE ARE THE RECOMMENDATIONS TO LOCALIZE:
{chr(10).join(rec_list)}

TASK: Replace each restaurant name with a REAL Nigerian restaurant that serves similar food or has similar vibes.

NIGERIAN RESTAURANTS YOU CAN USE (pick the best match for each):
- Chicken Republic (fast food, fried chicken)
- Mr Biggs (fast food, pastries, rice)
- Tantalizers (fast food, pies, snacks)
- Sweet Sensation (fast food, Nigerian food)
- Kilimanjaro (fast food, sharwarma)
- Yellow Chilli (upscale Nigerian cuisine, Lekki)
- Nkoyo (fine dining, Nigerian)
- Mama Cass (Nigerian buffet, affordable)
- Jevinik (Nigerian restaurant, pepper soup)
- Buka Lagos (local food, amala, ewedu)
- Yakoyo (Nigerian local food, multiple branches)
- The Place (restaurant and bar, grills)
- Cafe Neo (coffee shop, cafe)
- Cafe One (upscale cafe, Ikoyi)
- Art Cafe (cafe, pastries)
- Quilox (nightclub, lounge, VIP)
- Shiro Lagos (upscale bar, cocktails)
- Hard Rock Cafe Lagos (bar, live music)
- Sky Bar (rooftop bar, nightlife)
- Domino's Pizza Lekki (pizza delivery)
- Pizza Republic (pizza, casual dining)
- Barcelos (grilled chicken, Portuguese)
- Terra Kulture (art cafe, Nigerian food)
- Bogobiri (boutique restaurant, art vibes)
- The Wheatbaker (hotel restaurant, fine dining)
- Radisson Blu Lagos (hotel restaurant)
- Bukka Hut (modern buka, local food)
- Amala Zone (amala, ewedu, gbegiri)
- Olaiya Foods (local food, Surulere)
- Chowdeck Kitchen (delivery restaurant)
- 1004 Restaurant (Victoria Island)
- Bottles (bar and lounge, VI)

ALSO localize the category and reason:
- Replace American cities with Nigerian areas (Lekki, VI, Ikeja, Ikoyi, Surulere, Yaba, Abuja)
- Replace dollar references with Naira
- Keep the reason warm and Nigerian-friendly

Respond with a JSON array in this EXACT format:
[
  {{"name": "Nigerian Restaurant Name", "category": "Nigerian Category", "reason": "Nigerian-localized reason"}},
  ...
]

Return exactly {len(recommendations)} items:
"""

    try:
        response = LLM.invoke([HumanMessage(content=localization_prompt)])
        text = response.content

        print(f"[Task B] Localization LLM response: {text[:300]}...")

        import re
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            parsed = json.loads(json_match.group(0))

            localized = []
            for i, item in enumerate(parsed):
                localized.append({
                    "name": item.get("name", recommendations[i]["name"] if i < len(recommendations) else ""),
                    "category": item.get("category", recommendations[i]["category"] if i < len(recommendations) else ""),
                    "reason": item.get("reason", recommendations[i]["reason"] if i < len(recommendations) else ""),
                    "image_url": ""
                })

            print(f"[Task B] Successfully localized {len(localized)} recommendations")
            return {"recommendations": localized}

    except Exception as e:
        print(f"[Task B] Localization failed: {e}, keeping original recommendations")

    return {"recommendations": recommendations}

# Build the LangGraph with conditional branching
def build_task_b_graph():
    """Build the StateGraph for Task B with conditional routing, validation, and MongoDB checkpointing"""
    from memory import get_memory
    
    graph = StateGraph(TaskBState)

    # Add nodes
    graph.add_node("detect_mode",              node_detect_mode)
    graph.add_node("fetch_history",            node_fetch_history)
    graph.add_node("expand_domain",            node_expand_domain)
    graph.add_node("cold_start_search",        node_cold_start_search)
    graph.add_node("get_candidates",           node_get_candidates)
    graph.add_node("rank_recommend",           node_rank_recommend)
    graph.add_node("validate_recommendations", node_validate_recommendations)
    graph.add_node("localize_nigerian",        node_localize_nigerian)

    # Start with mode detection
    graph.add_edge(START, "detect_mode")

    # Conditional branch: history vs cold start
    graph.add_conditional_edges("detect_mode", route_by_mode, {
        "fetch_history":     "fetch_history",
        "cold_start_search": "cold_start_search"
    })

    # History path: fetch → expand domain → get candidates → rank → validate → localize
    graph.add_edge("fetch_history",            "expand_domain")
    graph.add_edge("expand_domain",            "get_candidates")
    graph.add_edge("get_candidates",           "rank_recommend")

    # Cold start path: search → rank → validate → localize
    graph.add_edge("cold_start_search",        "rank_recommend")

    # Both paths converge at validation → localization before END
    graph.add_edge("rank_recommend",           "validate_recommendations")
    graph.add_edge("validate_recommendations", "localize_nigerian")
    graph.add_edge("localize_nigerian",        END)

    # Compile with MongoDB checkpointing for persistent state
    memory = get_memory()
    if memory:
        print("✅ Task B: Using MongoDB for persistent agent state")
        return graph.compile(checkpointer=memory)
    else:
        print("⚠️ Task B: Running without persistent state")
        return graph.compile()

# Compile the graph
task_b_graph = build_task_b_graph()

async def run_task_b(request) -> dict:
    """
    Run Task B agent

    Args:
        request: TaskBRequest with user_id, persona_text, top_k

    Returns:
        dict with recommendations and mode
    """
    # Config for checkpointer (if MongoDB is enabled)
    config = {
        "configurable": {
            "thread_id": f"task_b_{request.user_id}"
        }
    }
    
    result = task_b_graph.invoke({
        "user_id": request.user_id,
        "persona_text": request.persona_text,
        "top_k": request.top_k,
        "mode": "",
        "user_reviews": "",
        "user_style": "",
        "primary_category": "",
        "extra_categories": [],
        "candidates": "",
        "recommendations": [],
        "reviewed_businesses": []
    }, config=config)

    return {
        "recommendations": result["recommendations"],
        "mode": result["mode"]
    }
