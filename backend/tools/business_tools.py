"""
Business Tools for LangChain Agents
Functions to fetch business/restaurant data
"""

from langchain.tools import tool
from database.db import get_business_info, get_businesses_not_reviewed_by_user

@tool
def fetch_business_info(business_name: str) -> str:
    """
    Look up a business or restaurant by name in the database.
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
    Returns up to 50 candidate businesses for recommendation.
    Use this as input for ranking and recommendation.
    For existing users with history only - NOT for cold-start users.
    """
    print(f"[Tool] get_candidate_businesses called with category: '{preferred_category}'")
    candidates = get_businesses_not_reviewed_by_user(user_id, preferred_category, limit=50)

    print(f"[Tool] get_candidate_businesses returned {len(candidates) if candidates else 0} businesses")

    if not candidates or len(candidates) == 0:
        print(f"[Tool] WARNING: No candidates found, returning error message")
        return "No unreviewed businesses found for this user."

    formatted = []
    for b in candidates:
        formatted.append(f"- {b['name']} | {b['categories']} | {b['stars']} stars | {b['city']}, {b['state']}")
    
    result = "\n".join(formatted)
    print(f"[Tool] Formatted {len(formatted)} businesses for LLM")
    return result
