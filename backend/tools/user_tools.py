"""
User Tools for LangChain Agents
Functions to fetch and analyze user data
"""

from langchain.tools import tool
from database.db import get_user_reviews, get_user_profile
from middleware.nigerian_localization import (
    get_pidgin_level,
    get_budget_consciousness,
    is_gen_z_tone
)

@tool
def fetch_user_reviews(user_id: str) -> str:
    """
    Fetch the past reviews written by this user from the database.
    Returns their review history including stars, text, and business names.
    Use this to understand the user's preferences, writing style, and rating behaviour.
    """
    reviews = get_user_reviews(user_id, limit=15)
    print(f"[Database] Fetched {len(reviews)} reviews for user {user_id}")

    if not reviews:
        return f"No reviews found for user {user_id}"

    formatted = []
    for i, r in enumerate(reviews):
        review_preview = r['text'][:200] if len(r['text']) > 200 else r['text']
        formatted.append(
            f"- {r['business_name']} ({r['categories']}): {r['stars']} stars\n  \"{review_preview}...\""
        )
        # Log first review sample
        if i == 0:
            print(f"[Database] Sample review: {r['stars']} stars - \"{review_preview[:80]}...\"")

    return "\n".join(formatted)

@tool
def analyze_user_style(user_id: str) -> str:
    """
    Analyze a user's reviewing patterns: average rating, tone, topics they care about,
    language style (formal, casual, Pidgin), Nigerian cultural elements, and what they
    praise or complain about most.
    Use this AFTER fetching reviews to build a user persona summary.
    """
    profile = get_user_profile(user_id)
    reviews = get_user_reviews(user_id, limit=15)

    # Handle None or missing profile data
    if not profile:
        profile = {}

    avg_stars = profile.get("computed_avg", 3.0) if profile.get("computed_avg") is not None else 3.0
    review_count = profile.get("total_reviews", 0) if profile.get("total_reviews") is not None else 0

    # Analyze Nigerian context usage
    pidgin_level = get_pidgin_level(reviews) or "None"
    budget_conscious = get_budget_consciousness(reviews) or "Unknown"
    gen_z = is_gen_z_tone(reviews)

    print(f"[Analysis] User avg: {avg_stars:.1f} stars, Pidgin: {pidgin_level}, Budget: {budget_conscious}, Gen Z: {gen_z}")

    style_summary = f"""
User Stats:
- Average rating: {avg_stars:.1f} stars
- Total reviews written: {review_count}
- Recent reviews sample: {len(reviews)} reviews fetched

Nigerian Context Analysis:
- Pidgin English usage: {pidgin_level}
- Budget consciousness: {budget_conscious}
- Gen Z tone: {"Yes" if gen_z else "No"}

Use the fetched reviews to determine:
1. Writing style (formal/casual/Pidgin English/Gen Z slang)
2. What they care about (price, service, food quality, ambience, speed, Nigerian food)
3. Emotional tone (harsh, neutral, enthusiastic)
4. Typical review length (short sentence vs long paragraph)
5. Nigerian cultural references they use
6. Mention of Naira/prices/value for money
"""
    return style_summary
