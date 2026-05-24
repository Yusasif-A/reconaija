"""
Nigerian Localization Middleware
Injects Nigerian cultural context, Pidgin English, and Gen Z vibes into LLM prompts
"""

NIGERIAN_CONTEXT = """
NIGERIAN LOCALIZATION RULES (CRITICAL - MUST FOLLOW):

**IMPORTANT: Location Rules**
- The data may show American cities (Saint Louis, Tucson, etc.) - IGNORE THEM
- If the user provided a specific location in the input (e.g. "Yakoyo, Ijesha"), use THAT EXACT location. Do NOT substitute it with Lekki, VI, or any other area.
- Only add a Nigerian city reference if no location is already in the business name
- Write as if you're a Nigerian recommending places to other Nigerians

**Cultural Context:**
- Reference Nigerian cities: Lagos (Lekki, VI, Ikeja), Abuja, Port Harcourt, Ibadan
- Nigerian food terms: jollof rice, suya, puff puff, chin chin, egusi soup, buka (local restaurant), mama put (street food vendor), amala, ewedu, pepper soup, small chops
- Mention Naira (₦) for prices and value-for-money concerns
- Reference popular Nigerian spots: Shoprite, Game, Mr Biggs, Chicken Republic, Tantalizers

**Pidgin English Phrases (Use naturally based on user style):**
- "e don do" (it's enough/done)
- "no be small thing" (it's a big deal)
- "correct" (good/excellent)
- "sharp sharp" (quickly)
- "e be like say" (it seems like)
- "dem no try" (they didn't do well)
- "e dey" (it's there/available)
- "wetin" (what)
- "abeg" (please)
- "omo" (wow/oh my)
- "wahala" (trouble/problem)
- "ginger" (energy/enthusiasm)
- "vibes" (atmosphere/mood)
- "chop" (eat)
- "belle full" (satisfied/full)
- "no wahala" (no problem)

**Gen Z Nigerian Tone:**
- Use modern slang: "lowkey", "highkey", "no cap", "hits different"
- Express enthusiasm: "this place is giving!", "the vibes are immaculate"
- Be authentic and relatable
- Mix English with Pidgin naturally
- Reference social media culture when relevant

**Affordability & Value:**
- Nigerians are price-conscious - mention value for money
- Reference "affordable", "budget-friendly", "worth the price"
- Compare prices to expectations
- Mention if something is "expensive" or "cheap"

**IMPORTANT RULES:**
1. Only use Pidgin if the user's review history shows they write that way
2. Never force Pidgin on users who write formal English
3. Keep Nigerian references natural and relevant to the context
4. Match the user's existing tone and style first
5. Gen Z tone is for younger users (based on their review style)
6. Don't overdo it - subtle integration is better than heavy-handed

**For Recommendations:**
- Use warm, friendly Nigerian communication style
- Emphasize community and social aspects
- Mention if a place is "popular" or "trending"
- Reference if it's good for "hangout", "dates", "family time"
- Consider safety and location accessibility
"""

def inject_nigerian_context(base_prompt: str) -> str:
    """
    Inject Nigerian localization context into any LLM prompt

    Args:
        base_prompt: The original prompt

    Returns:
        Enhanced prompt with Nigerian context
    """
    return base_prompt + "\n\n" + NIGERIAN_CONTEXT

def get_pidgin_level(user_reviews: list[dict]) -> str:
    """
    Analyze user's reviews to determine their Pidgin usage level

    Args:
        user_reviews: List of user's past reviews

    Returns:
        "none", "light", "medium", or "heavy"
    """
    if not user_reviews:
        return "none"

    pidgin_indicators = [
        "e don", "no be", "wetin", "abeg", "omo", "wahala",
        "dem no", "e be like", "sharp sharp", "correct", "e dey"
    ]

    total_reviews = len(user_reviews)
    pidgin_count = 0

    for review in user_reviews:
        text = review.get('text', '').lower()
        if any(indicator in text for indicator in pidgin_indicators):
            pidgin_count += 1

    pidgin_ratio = pidgin_count / total_reviews if total_reviews > 0 else 0

    if pidgin_ratio == 0:
        return "none"
    elif pidgin_ratio < 0.3:
        return "light"
    elif pidgin_ratio < 0.6:
        return "medium"
    else:
        return "heavy"

def get_budget_consciousness(user_reviews: list[dict]) -> str:
    """
    Determine if user is budget-conscious based on their reviews

    Args:
        user_reviews: List of user's past reviews

    Returns:
        "high", "medium", or "low"
    """
    if not user_reviews:
        return "medium"

    price_indicators = [
        "price", "expensive", "cheap", "affordable", "value", "worth",
        "money", "cost", "budget", "naira", "₦"
    ]

    total_reviews = len(user_reviews)
    price_mention_count = 0

    for review in user_reviews:
        text = review.get('text', '').lower()
        if any(indicator in text for indicator in price_indicators):
            price_mention_count += 1

    price_ratio = price_mention_count / total_reviews if total_reviews > 0 else 0

    if price_ratio > 0.5:
        return "high"
    elif price_ratio > 0.2:
        return "medium"
    else:
        return "low"

def is_gen_z_tone(user_reviews: list[dict]) -> bool:
    """
    Determine if user uses Gen Z tone/slang

    Args:
        user_reviews: List of user's past reviews

    Returns:
        True if Gen Z tone detected
    """
    if not user_reviews:
        return False

    gen_z_indicators = [
        "lowkey", "highkey", "no cap", "vibes", "hits different",
        "giving", "immaculate", "fr", "tbh", "ngl", "slay"
    ]

    for review in user_reviews:
        text = review.get('text', '').lower()
        if any(indicator in text for indicator in gen_z_indicators):
            return True

    return False
