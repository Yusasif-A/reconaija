"""
Recommendation Tools for LangChain Agents
Functions for vector search and ranking
"""

from langchain.tools import tool
from embeddings.vector_store import search_similar_businesses

@tool
def vector_search_businesses(query: str, top_k: int = 10) -> str:
    """
    ONLY USE THIS FOR COLD-START USERS (no user_id, free text persona only).
    Search for businesses semantically similar to a query description using vector embeddings.

    Example queries:
    - "affordable Nigerian restaurants with good jollof rice"
    - "upscale dining in Lagos with great ambience"
    - "cheap fast food with good service"

    For existing users with history, use get_candidate_businesses (SQL) instead — it is faster and more accurate.
    Returns a ranked list of matching businesses.
    """
    results = search_similar_businesses(query, top_k=top_k)
    if not results:
        return "No matching businesses found."

    formatted = []
    for r in results:
        formatted.append(
            f"- {r['name']} | {r['categories']} | {r['stars']} stars | {r['city']}, {r['state']} | Match Score: {r['similarity']:.2f}"
        )
    return "\n".join(formatted)

@tool
def rank_and_explain(user_preferences: str, candidates: str) -> str:
    """
    Final reasoning step for recommendations.
    Given a summary of user preferences and a list of candidate businesses,
    rank the candidates from most to least suitable and explain why each fits.

    Use this AFTER either:
    - get_candidate_businesses (existing user) OR
    - vector_search_businesses (cold-start)

    Input user_preferences as a text summary.
    Input candidates as the raw list from the previous tool.

    Output should be Nigerian-friendly with warm, relatable tone.
    """
    return f"""
Task: Rank these candidates for a user with these preferences.

User Preferences:
{user_preferences}

Candidates:
{candidates}

Please rank them 1–5 (or up to top_k), give each a score out of 10, and explain in 1–2 sentences
why it suits this user.

Use a warm, friendly Nigerian tone. Consider:
- Value for money (important in Nigerian context)
- Food quality (especially Nigerian dishes if relevant)
- Service and ambience
- Location accessibility
- Social/hangout vibes

Write explanations that feel natural and relatable, mixing English with light Pidgin if appropriate.
"""
