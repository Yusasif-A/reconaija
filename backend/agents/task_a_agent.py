"""
Task A Agent - User Modeling
Simulates how a specific user would review a restaurant using LangGraph
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from config import LLM
from tools.user_tools import fetch_user_reviews, analyze_user_style
from tools.business_tools import fetch_business_info
from middleware.nigerian_localization import inject_nigerian_context

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
    needs_reflection: bool  # filled by node 5

# Node 1: Fetch user past reviews from MySQL
def node_fetch_reviews(state: TaskAState) -> dict:
    """Fetch user's review history"""
    print("[Task A] Node: fetch_reviews - Getting user review history")
    reviews = fetch_user_reviews.invoke({"user_id": state["user_id"]})
    return {"user_reviews": reviews}

# Node 2: Analyze user writing style
def node_analyze_style(state: TaskAState) -> dict:
    """Analyze user's writing patterns and Nigerian context usage"""
    print("[Task A] Node: analyze_style - Analyzing user writing patterns")
    style = analyze_user_style.invoke({"user_id": state["user_id"]})
    return {"user_style": style}

# Node 3: Fetch target business info from MySQL
def node_fetch_business(state: TaskAState) -> dict:
    """Get information about the target restaurant/business"""
    print("[Task A] Node: fetch_business - Getting target business information")
    info = fetch_business_info.invoke({"business_name": state["product_name"]})
    return {"business_info": info}

# Node 4: LLM generates the simulated review
def node_generate_review(state: TaskAState) -> dict:
    """Generate review matching user's style with Nigerian context"""
    print("[Task A] Node: generate_review - Generating review with LLM")

    # Check if this is a Nigerian-themed demo user (persona override)
    persona_override = ""
    has_no_history = "No reviews found" in state.get("user_reviews", "")

    if state.get("persona_text"):
        persona_lower = state["persona_text"].lower()
        if "pidgin" in persona_lower:
            history_note = "The user has no review history, so create a typical review for this persona." if has_no_history else "IGNORE the formal English in their review history. That's just sample data."
            persona_override = f"""
CRITICAL INSTRUCTION - PERSONA OVERRIDE:
This user is "The Pidgin Pro" - they write HEAVILY in Nigerian Pidgin English.
{history_note}
You MUST write this review in authentic Nigerian Pidgin English throughout.

Examples of Pidgin phrases to use:
- "Dis place dey kampe!" (This place is great!)
- "E no make sense at all" (It doesn't make sense)
- "The food sweet die" (The food is very delicious)
- "Na correct place be this" (This is a proper place)
- "Service dey very slow" (Service is very slow)
- "Price no too high" (Price is not too high)
- "I go come back again" (I will come back again)
- "E be like say..." (It seems like...)
- "Them sabi cook well well" (They cook very well)

Write the ENTIRE review in Pidgin, not just phrases here and there.
"""
        elif "budget" in persona_lower or "king" in persona_lower:
            history_note = "The user has no review history, so give a rating around 3-4 stars." if has_no_history else ""
            persona_override = f"""
CRITICAL INSTRUCTION - PERSONA OVERRIDE:
This user is "The Budget King" - they are VERY price-conscious.
{history_note}
MUST mention prices, value for money, affordability in EVERY review.
Compare prices, mention if it's worth the Naira, talk about cheaper alternatives.
"""
        elif "harsh" in persona_lower or "critic" in persona_lower:
            history_note = "The user has no review history, so give LOW ratings (1-2 stars)." if has_no_history else ""
            persona_override = f"""
CRITICAL INSTRUCTION - PERSONA OVERRIDE:
This user is "The Harsh Critic" - they give LOW ratings (1-2 stars typically).
{history_note}
Be critical, blunt, and point out flaws. Don't be generous with stars.
"""
        elif "hype" in persona_lower:
            history_note = "The user has no review history, so give HIGH ratings (4-5 stars)." if has_no_history else ""
            persona_override = f"""
CRITICAL INSTRUCTION - PERSONA OVERRIDE:
This user is "The Hype Man" - they give HIGH ratings (4-5 stars always).
{history_note}
Be enthusiastic, positive, and excited. Everything is amazing!
"""
        elif "foodie" in persona_lower or "lagos" in persona_lower:
            history_note = "The user has no review history, so give ratings around 4-5 stars." if has_no_history else ""
            persona_override = f"""
CRITICAL INSTRUCTION - PERSONA OVERRIDE:
This user is "The Lagos Foodie" - they love upscale dining and write detailed reviews.
{history_note}
Be sophisticated, mention ambience, presentation, and fine dining experience.
Give high ratings (4-5 stars) for quality places.
"""

    # Adjust instructions based on whether user has history
    if has_no_history:
        rating_instruction = "Follow the persona override instructions for star rating."
        style_instruction = "Create a review that matches the persona described above."
        length_instruction = "Write 2-3 sentences (typical Nigerian review length)."
    else:
        rating_instruction = "Match their typical star rating behaviour (check their average in the analysis)."
        style_instruction = "Use their exact tone and language style from the review history."
        length_instruction = "Keep length similar to their usual reviews."

    base_prompt = f"""
You are simulating a review written by a specific user for a restaurant/business.

{persona_override}

USER REVIEW HISTORY:
{state['user_reviews']}

USER STYLE ANALYSIS:
{state['user_style']}

TARGET BUSINESS:
{state['business_info']}
Name: {state['product_name']} | Category: {state['product_category']}

TASK: Generate the review this user would write for the target business.

Requirements:
- {rating_instruction}
- {style_instruction}
- If persona override is specified above, FOLLOW IT EXACTLY - it overrides review history
- If they're budget-conscious, mention prices/value for money
- If they use Gen Z slang, incorporate it naturally
- Mention what they usually care about (service, food quality, ambience, speed, etc.)
- {length_instruction}
- IMPORTANT: If the business name includes a location (e.g. "Yakoyo, Ijesha"), use THAT location. Do NOT substitute a different area.
- Add Nigerian context naturally where appropriate (Naira, local food terms)

Respond in EXACTLY this format:
STARS: [1-5]
REVIEW: [the full review text - make it authentic to this user's voice]
STYLE_NOTE: [one sentence describing the user style you captured, including Nigerian elements if present]
"""

    # Inject Nigerian localization context
    enhanced_prompt = inject_nigerian_context(base_prompt)

    # Call LLM
    response = LLM.invoke([HumanMessage(content=enhanced_prompt)])
    text = response.content

    # Parse response
    stars, review, style_note = 3, "", ""
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("STARS:"):
            try:
                stars = int(line.replace("STARS:", "").strip())
            except:
                stars = 3
        elif line.startswith("REVIEW:"):
            review = line.replace("REVIEW:", "").strip()
        elif line.startswith("STYLE_NOTE:"):
            style_note = line.replace("STYLE_NOTE:", "").strip()

    # If review is still empty, take everything after "REVIEW:" as multiline
    if not review:
        in_review = False
        review_lines = []
        for line in lines:
            if line.startswith("REVIEW:"):
                in_review = True
                review_lines.append(line.replace("REVIEW:", "").strip())
            elif in_review and not line.startswith("STYLE_NOTE:"):
                review_lines.append(line)
            elif line.startswith("STYLE_NOTE:"):
                break
        review = " ".join(review_lines).strip()

    return {"stars": stars, "review_text": review, "style_note": style_note}

# Node 5: Reflect and improve the generated review
def node_reflect_and_improve(state: TaskAState) -> dict:
    """Self-check the generated review for consistency with user style"""
    print("[Task A] Node: reflect_and_improve - Validating review consistency")

    # Extract user's average rating from style analysis
    user_avg = 3.0
    if "average" in state["user_style"].lower() or "avg" in state["user_style"].lower():
        import re
        match = re.search(r'(\d+\.?\d*)\s*stars?', state["user_style"])
        if match:
            user_avg = float(match.group(1))

    # Check if review needs improvement
    star_diff = abs(state["stars"] - user_avg)
    needs_check = star_diff > 1.5  # More than 1.5 stars difference is suspicious

    if not needs_check:
        # Review looks good, return as-is
        return {"needs_reflection": False}

    # Review needs improvement - ask LLM to reflect and fix
    reflection_prompt = f"""
You generated this review, but it may not match the user's typical style. Please review and improve it.

USER'S TYPICAL STYLE:
{state['user_style']}

GENERATED REVIEW:
Stars: {state['stars']}
Review: {state['review_text']}

ISSUE DETECTED:
The star rating ({state['stars']}) differs significantly from the user's average ({user_avg:.1f} stars).

TASK: Check if the rating and review text are consistent with this user's typical behavior.
- If the user is generally positive (avg > 4), they rarely give 1-2 stars
- If the user is generally critical (avg < 3), they rarely give 5 stars
- The review tone should match the star rating

If correction is needed, rewrite the review to be more consistent with their style.
If it's actually correct (e.g., they had a genuinely bad/good experience), keep it.

Respond in EXACTLY this format:
STARS: [1-5]
REVIEW: [the corrected or original review text]
REFLECTION: [one sentence explaining if you changed it and why]
"""

    # Inject Nigerian context
    enhanced_prompt = inject_nigerian_context(reflection_prompt)

    # Call LLM
    response = LLM.invoke([HumanMessage(content=enhanced_prompt)])
    text = response.content

    # Parse response
    new_stars, new_review, reflection = state["stars"], state["review_text"], ""
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("STARS:"):
            try:
                new_stars = int(line.replace("STARS:", "").strip())
            except:
                pass
        elif line.startswith("REVIEW:"):
            new_review = line.replace("REVIEW:", "").strip()
        elif line.startswith("REFLECTION:"):
            reflection = line.replace("REFLECTION:", "").strip()

    # If review is multiline
    if not new_review or len(new_review) < 20:
        in_review = False
        review_lines = []
        for line in lines:
            if line.startswith("REVIEW:"):
                in_review = True
                review_lines.append(line.replace("REVIEW:", "").strip())
            elif in_review and not line.startswith("REFLECTION:"):
                review_lines.append(line)
            elif line.startswith("REFLECTION:"):
                break
        if review_lines:
            new_review = " ".join(review_lines).strip()

    return {
        "stars": new_stars,
        "review_text": new_review,
        "style_note": state["style_note"] + f" | Reflection: {reflection}",
        "needs_reflection": True
    }

# Build the LangGraph
def build_task_a_graph():
    """Build the StateGraph for Task A with MongoDB checkpointing"""
    from memory import get_memory
    
    graph = StateGraph(TaskAState)

    # Add nodes
    graph.add_node("fetch_reviews",          node_fetch_reviews)
    graph.add_node("analyze_style",          node_analyze_style)
    graph.add_node("fetch_business",         node_fetch_business)
    graph.add_node("generate_review",        node_generate_review)
    graph.add_node("reflect_and_improve",    node_reflect_and_improve)

    # Add edges (linear flow with reflection)
    graph.add_edge(START,                    "fetch_reviews")
    graph.add_edge("fetch_reviews",          "analyze_style")
    graph.add_edge("analyze_style",          "fetch_business")
    graph.add_edge("fetch_business",         "generate_review")
    graph.add_edge("generate_review",        "reflect_and_improve")
    graph.add_edge("reflect_and_improve",    END)

    # Compile with MongoDB checkpointing for persistent state
    memory = get_memory()
    if memory:
        print("✅ Task A: Using MongoDB for persistent agent state")
        return graph.compile(checkpointer=memory)
    else:
        print("⚠️ Task A: Running without persistent state")
        return graph.compile()

# Compile the graph
task_a_graph = build_task_a_graph()

async def run_task_a(request) -> dict:
    """
    Run Task A agent

    Args:
        request: TaskARequest with user_id, persona_text, product_name, product_category

    Returns:
        dict with stars, review_text, user_style_summary
    """
    # Config for checkpointer (if MongoDB is enabled)
    config = {
        "configurable": {
            "thread_id": f"task_a_{request.user_id}_{request.product_name}"
        }
    }
    
    result = task_a_graph.invoke({
        "user_id": request.user_id,
        "persona_text": request.persona_text,
        "product_name": request.product_name,
        "product_category": request.product_category,
        "user_reviews": "",
        "user_style": "",
        "business_info": "",
        "stars": 3,
        "review_text": "",
        "style_note": "",
        "needs_reflection": False
    }, config=config)

    return {
        "stars": result["stars"],
        "review_text": result["review_text"],
        "user_style_summary": result["style_note"]
    }
