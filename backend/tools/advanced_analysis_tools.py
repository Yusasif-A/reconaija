"""
Advanced Analysis Tools for Enhanced Agent Architecture
Specialized tools for deeper review analysis and personality extraction
"""

from langchain.tools import tool
from database.db import get_user_reviews
from middleware.nigerian_localization import get_pidgin_level, get_budget_consciousness, is_gen_z_tone

@tool
def extract_personality_traits(user_id: str) -> str:
    """
    Extract detailed personality traits from user's review history.
    Analyzes sentiment patterns, emotional expression, and psychological indicators.

    Returns personality profile including:
    - Optimism level (pessimist/realist/optimist)
    - Detail orientation (brief/moderate/detailed)
    - Emotional expression (reserved/balanced/expressive)
    - Social orientation (solo/casual/social butterfly)
    """
    reviews = get_user_reviews(user_id, limit=15)
    if not reviews:
        return "Insufficient review history for personality extraction"

    # Analyze sentiment patterns
    positive_words = ["great", "excellent", "amazing", "love", "perfect", "wonderful", "fantastic"]
    negative_words = ["bad", "terrible", "awful", "worst", "horrible", "disappointing", "poor"]

    positive_count = 0
    negative_count = 0
    total_words = 0
    detail_scores = []

    for review in reviews:
        text = review.get('text', '').lower()
        words = text.split()
        total_words += len(words)
        detail_scores.append(len(words))

        for word in words:
            if word in positive_words:
                positive_count += 1
            if word in negative_words:
                negative_count += 1

    # Calculate traits
    avg_length = sum(detail_scores) / len(detail_scores) if detail_scores else 0

    if positive_count > negative_count * 2:
        optimism = "optimist"
    elif negative_count > positive_count * 2:
        optimism = "pessimist"
    else:
        optimism = "realist"

    if avg_length < 30:
        detail_level = "brief"
    elif avg_length < 80:
        detail_level = "moderate"
    else:
        detail_level = "detailed"

    emotion_ratio = (positive_count + negative_count) / total_words if total_words > 0 else 0
    if emotion_ratio > 0.05:
        emotional = "expressive"
    elif emotion_ratio > 0.02:
        emotional = "balanced"
    else:
        emotional = "reserved"

    return f"""
Personality Profile:
- Optimism Level: {optimism}
- Detail Orientation: {detail_level}
- Emotional Expression: {emotional}
- Average Review Length: {avg_length:.0f} words
- Sentiment Ratio: {positive_count} positive / {negative_count} negative expressions
"""

@tool
def detect_review_tone(user_id: str) -> str:
    """
    Detect the dominant tone and voice in user's reviews.
    Identifies writing style patterns including formality, humor, and cultural elements.

    Returns tone analysis:
    - Formality level (casual/semi-formal/formal)
    - Humor usage (none/occasional/frequent)
    - Nigerian cultural elements (none/light/moderate/heavy)
    - Critique style (constructive/balanced/harsh)
    """
    reviews = get_user_reviews(user_id, limit=15)
    if not reviews:
        return "Insufficient review history for tone detection"

    # Analyze formality
    formal_indicators = ["however", "therefore", "furthermore", "nevertheless", "consequently"]
    casual_indicators = ["gonna", "wanna", "yeah", "nah", "lol", "tbh", "fr"]
    humor_indicators = ["haha", "lol", "funny", "hilarious", "joke", "😂", "😄"]

    formal_count = 0
    casual_count = 0
    humor_count = 0

    pidgin_level = get_pidgin_level(reviews)

    for review in reviews:
        text = review.get('text', '').lower()

        for indicator in formal_indicators:
            if indicator in text:
                formal_count += 1

        for indicator in casual_indicators:
            if indicator in text:
                casual_count += 1

        for indicator in humor_indicators:
            if indicator in text:
                humor_count += 1

    # Determine formality
    if formal_count > casual_count:
        formality = "formal"
    elif casual_count > formal_count * 2:
        formality = "casual"
    else:
        formality = "semi-formal"

    # Determine humor
    if humor_count == 0:
        humor = "none"
    elif humor_count < len(reviews) * 0.3:
        humor = "occasional"
    else:
        humor = "frequent"

    # Map Pidgin level to cultural elements
    cultural_map = {
        "none": "none",
        "light": "light",
        "medium": "moderate",
        "heavy": "heavy"
    }
    cultural = cultural_map.get(pidgin_level, "none")

    return f"""
Tone Analysis:
- Formality Level: {formality}
- Humor Usage: {humor}
- Nigerian Cultural Elements: {cultural} (Pidgin: {pidgin_level})
- Gen Z Tone: {"Yes" if is_gen_z_tone(reviews) else "No"}
- Budget Consciousness: {get_budget_consciousness(reviews)}
"""

@tool
def predict_rating_tendency(user_id: str) -> str:
    """
    Predict user's rating tendencies and patterns.
    Analyzes historical rating behavior to forecast likely ratings.

    Returns prediction model:
    - Average rating
    - Rating distribution
    - Leniency score (harsh/balanced/lenient)
    - Consistency score (consistent/variable)
    """
    reviews = get_user_reviews(user_id, limit=15)
    if not reviews:
        return "Insufficient review history for rating prediction"

    ratings = [r.get('stars', 3) for r in reviews]
    avg_rating = sum(ratings) / len(ratings) if ratings else 3.0

    # Rating distribution
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating in ratings:
        rating_counts[rating] = rating_counts.get(rating, 0) + 1

    # Leniency
    if avg_rating >= 4.0:
        leniency = "lenient"
    elif avg_rating <= 2.5:
        leniency = "harsh"
    else:
        leniency = "balanced"

    # Consistency (standard deviation)
    variance = sum((r - avg_rating) ** 2 for r in ratings) / len(ratings) if ratings else 0
    std_dev = variance ** 0.5

    if std_dev < 0.8:
        consistency = "consistent"
    else:
        consistency = "variable"

    distribution = ", ".join([f"{star}★: {count}" for star, count in sorted(rating_counts.items())])

    return f"""
Rating Prediction Model:
- Average Rating: {avg_rating:.1f} stars
- Distribution: {distribution}
- Leniency: {leniency}
- Consistency: {consistency} (std dev: {std_dev:.2f})
- Most Common Rating: {max(rating_counts, key=rating_counts.get)}★
- Rating Range: {min(ratings)}★ to {max(ratings)}★
"""

@tool
def analyze_review_topics(user_id: str) -> str:
    """
    Analyze key topics and themes in user's reviews.
    Identifies what aspects of dining experience the user focuses on.

    Returns topic analysis:
    - Primary focus areas (food/service/ambience/price/speed)
    - Mentioned aspects frequency
    - Priorities ranking
    """
    reviews = get_user_reviews(user_id, limit=15)
    if not reviews:
        return "Insufficient review history for topic analysis"

    # Topic keywords
    topics = {
        "food_quality": ["food", "taste", "flavor", "delicious", "dish", "meal", "cook", "jollof", "suya"],
        "service": ["service", "staff", "waiter", "waitress", "server", "friendly", "rude", "attentive"],
        "ambience": ["atmosphere", "ambience", "vibe", "decor", "music", "lighting", "clean", "dirty"],
        "price": ["price", "expensive", "cheap", "affordable", "value", "money", "naira", "₦", "cost"],
        "speed": ["fast", "slow", "quick", "wait", "time", "long", "sharp sharp"],
        "location": ["location", "parking", "access", "lagos", "abuja", "lekki", "vi"]
    }

    topic_counts = {topic: 0 for topic in topics}

    for review in reviews:
        text = review.get('text', '').lower()
        for topic, keywords in topics.items():
            for keyword in keywords:
                if keyword in text:
                    topic_counts[topic] += 1
                    break  # Count once per review per topic

    # Sort by frequency
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

    # Format results
    topic_analysis = []
    for topic, count in sorted_topics:
        if count > 0:
            percentage = (count / len(reviews)) * 100
            topic_analysis.append(f"- {topic.replace('_', ' ').title()}: {count}/{len(reviews)} reviews ({percentage:.0f}%)")

    primary_focus = sorted_topics[0][0].replace('_', ' ').title() if sorted_topics[0][1] > 0 else "General"

    return f"""
Topic Analysis:
Primary Focus: {primary_focus}

Mentioned Aspects:
{chr(10).join(topic_analysis) if topic_analysis else "- No specific focus detected"}

Priority Ranking:
1. {sorted_topics[0][0].replace('_', ' ').title()}
2. {sorted_topics[1][0].replace('_', ' ').title()}
3. {sorted_topics[2][0].replace('_', ' ').title()}
"""

@tool
def generate_user_summary(user_id: str) -> str:
    """
    Generate a comprehensive one-paragraph summary of the user.
    Combines all analysis tools for a complete user profile.

    This is a meta-tool that synthesizes insights from:
    - Personality traits
    - Tone detection
    - Rating tendencies
    - Topic analysis
    - Nigerian cultural elements
    """
    reviews = get_user_reviews(user_id, limit=15)
    if not reviews:
        return "Insufficient review history for comprehensive summary"

    # Get quick insights
    pidgin = get_pidgin_level(reviews)
    budget = get_budget_consciousness(reviews)
    gen_z = is_gen_z_tone(reviews)

    ratings = [r.get('stars', 3) for r in reviews]
    avg_rating = sum(ratings) / len(ratings) if ratings else 3.0

    # Determine personality type
    if avg_rating >= 4.0 and pidgin in ["medium", "heavy"]:
        personality = "enthusiastic Naija foodie who loves sharing positive vibes"
    elif avg_rating <= 2.5:
        personality = "discerning critic with high standards"
    elif budget == "high":
        personality = "value-conscious reviewer who prioritizes affordability"
    elif gen_z:
        personality = "Gen Z trendsetter with modern tastes"
    else:
        personality = "balanced reviewer with moderate expectations"

    return f"""
User Summary:
This user is a {personality}. They typically give {avg_rating:.1f} stars on average.
{"They write in Nigerian Pidgin English, adding authentic local flavor to their reviews. " if pidgin != "none" else ""}
{"They're very price-conscious and often mention value for money. " if budget == "high" else ""}
{"They use Gen Z slang and modern expressions. " if gen_z else ""}
Based on {len(reviews)} reviews, they {"tend to be positive and encouraging" if avg_rating >= 4.0 else "tend to be critical and detailed" if avg_rating <= 2.5 else "provide balanced, fair assessments"}.
"""
