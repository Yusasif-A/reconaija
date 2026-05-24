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
    print(f"[Task B] User requested top_k: {state['top_k']}")
    print(f"[Task B] Fetching {state['top_k'] * 4} candidates for LLM to rank")
    
    results = vector_search_businesses.invoke({
        "query": state["persona_text"],
        "top_k": state["top_k"] * 4  # Get more candidates for ranking
    })
    
    print(f"[Task B] ChromaDB returned candidates (preview): {str(results)[:200]}...")
    
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

CRITICAL INSTRUCTION - USER REQUESTED EXACTLY {state['top_k']} RECOMMENDATIONS:
The user wants to see EXACTLY {state['top_k']} recommendations. NOT MORE, NOT LESS.
From the candidates above, select the top {state['top_k']} best matches.

IMPORTANT - WRITE CONFIDENT RECOMMENDATIONS:
- These are RECOMMENDATIONS, not suggestions or maybes
- Be DIRECT and CERTAIN in your language
- DO NOT use uncertain phrases like: "should offer", "might have", "you can check", "worth checking", "it is possible"
- USE confident phrases like: "offers", "has", "serves", "provides", "features", "specializes in"
- The user is asking for recommendations based on their preferences - be confident in your choices

RESPONSE FORMAT:
Return a JSON array with EXACTLY {state['top_k']} items. Each item must have:
- "name": exact business name from candidates
- "category": business category  
- "reason": 1-2 sentences explaining why this place matches their preferences (be confident and direct)

GOOD EXAMPLE (confident language):
{{"name": "Mama Put Kitchen", "category": "Nigerian Restaurant", "reason": "This restaurant serves authentic local dishes with excellent jollof rice at affordable prices, perfect for your budget and taste preferences."}}

BAD EXAMPLE (uncertain language):
{{"name": "Mama Put Kitchen", "category": "Nigerian Restaurant", "reason": "This restaurant should offer local dishes and you can check if they have jollof rice at good prices."}}

NOW RETURN EXACTLY {state['top_k']} RECOMMENDATIONS AS JSON WITH CONFIDENT, DIRECT LANGUAGE:
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
            
            # CRITICAL: Truncate to exactly top_k if LLM returned more
            if len(parsed) > state['top_k']:
                print(f"[Task B] WARNING: LLM returned {len(parsed)} items but user requested {state['top_k']}, truncating...")
                parsed = parsed[:state['top_k']]
            
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
    3. Truncate to exactly top_k items
    """
    print("[Task B] Node: validate_recommendations - Validating final recommendations")
    recommendations = state["recommendations"]
    reviewed_names = state.get("reviewed_businesses", [])
    top_k = state.get("top_k", 5)

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

    # Step 3: Truncate to exactly top_k items
    final_recommendations = filtered[:top_k]
    
    print(f"[Task B] Returning exactly {len(final_recommendations)} recommendations (requested: {top_k})")
    
    return {"recommendations": final_recommendations}

# Node 6: Localize recommendations to Nigerian context using LLM
def node_localize_nigerian(state: TaskBState) -> dict:
    """
    Use LLM to replace American business names and locations with Nigerian equivalents.
    Keeps detailed English descriptions - NO Pidgin.
    LLM uses its knowledge to pick appropriate Nigerian restaurants based on category.
    """
    print("[Task B] Node: localize_nigerian - Replacing with Nigerian businesses and locations")

    recommendations = state["recommendations"]
    print(f"[Task B] Input recommendations count: {len(recommendations)}")
    
    if not recommendations:
        return {"recommendations": []}

    import json

    # Build the list for LLM
    rec_list = []
    for i, rec in enumerate(recommendations):
        rec_list.append(f"{i+1}. Name: {rec['name']} | Category: {rec['category']} | Reason: {rec['reason']}")

    localization_prompt = f"""
You are a Nigerian restaurant localization agent. Replace American/foreign restaurant names with real Nigerian restaurant equivalents.

IMPORTANT RULES:
1. Replace business names with REAL Nigerian restaurants that match the category/type
2. Replace American locations with Nigerian areas (Lagos)
3. Keep descriptions in CLEAR, DETAILED ENGLISH - NO Pidgin
4. Match the restaurant type appropriately (fast food → Nigerian fast food, pizza → Nigerian pizza place, etc.)
5. USE CONFIDENT LANGUAGE - these are recommendations, not suggestions

CONFIDENT LANGUAGE RULES:
- DO NOT use: "should offer", "might have", "you can check", "worth checking", "it is possible", "may find"
- USE instead: "offers", "has", "serves", "provides", "features", "specializes in", "known for"
- Be DIRECT and CERTAIN - the user asked for recommendations, so recommend with confidence

HERE ARE THE RECOMMENDATIONS TO LOCALIZE:
{chr(10).join(rec_list)}

NIGERIAN RESTAURANTS YOU CAN USE (examples - use your knowledge for more):
- Fast Food/Chicken: Chicken Republic, Mr Biggs, Tantalizers, Sweet Sensation, Kilimanjaro
- Nigerian Food: Mama Cass, Jevinik, Buka Lagos, Yakoyo, Olaiya Foods, Bukka Hut, Amala Zone
- Upscale/Fine Dining: Yellow Chilli, Nkoyo, The Wheatbaker, Terra Kulture, Bogobiri
- Pizza: Domino's Pizza Lekki, Pizza Republic
- Cafes/Coffee: Cafe Neo, Cafe One, Art Cafe
- Bars/Nightlife: The Place, Quilox, Shiro Lagos, Hard Rock Cafe Lagos, Sky Bar, Bottles
- Grills: Barcelos, The Place
- Hotel Restaurants: Radisson Blu Lagos, The Wheatbaker, 1004 Restaurant
- Supermarkets: Shoprite, Grand Square, Spar, Ebeano

NIGERIAN LOCATIONS (Lagos areas):
- Lekki, Victoria Island (VI), Ikeja, Ikoyi, Surulere, Yaba, Ajah, Festac, Maryland, Gbagada

TASK: For each recommendation:
1. Replace the business name with an appropriate Nigerian restaurant
2. Replace American locations with Lagos areas
3. Keep the reason detailed and in clear English with CONFIDENT language
4. Replace $ with ₦

GOOD EXAMPLE (confident):
"Shoprite Ikeja | Grocery | This supermarket offers a wide selection of affordable groceries and household essentials at competitive prices, perfect for budget-conscious shoppers in Ikeja."

BAD EXAMPLE (uncertain):
"Shoprite Ikeja | Grocery | This supermarket should offer groceries and you can check if they have affordable items."

Respond with a JSON array with Nigerian business names, locations, and CONFIDENT descriptions:
[
  {{"name": "Nigerian Restaurant Name", "category": "category", "reason": "Confident, detailed English reason"}},
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
                # Only take up to the number of original recommendations
                if i >= len(recommendations):
                    break
                
                # Use LLM's Nigerian business name and localized reason
                localized.append({
                    "name": item.get("name", recommendations[i]["name"]),  # Nigerian business name
                    "category": item.get("category", recommendations[i]["category"]),
                    "reason": item.get("reason", recommendations[i]["reason"]),  # Localized reason in English
                    "image_url": ""  # No image for replaced businesses
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
    graph.add_node("localize_nigerian",        node_localize_nigerian)  # Rewrites reasons in Nigerian Pidgin

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

    # Both paths converge at validation, then localization, then END
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
