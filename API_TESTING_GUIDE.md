# RecoNaija API Testing Guide

This guide helps to test the API through Swagger UI or curl commands.

---

## Accessing Swagger UI

Once the backend is running, visit:
```
http://localhost:8000/docs
```

Or on Render:
```
https://reconaija.onrender.com/docs
```

---

## Task A: Generate Review

### Test Case 1: Existing User with Pidgin Override
```json
{
  "user_id": "user_001",
  "persona_text": "Pidgin Pro",
  "product_name": "Chicken Republic",
  "product_category": "Fast Food"
}
```

**Expected Output:**
- Review in Nigerian Pidgin English
- Star rating matching user's typical behavior
- References to Nigerian context (Naira, Lagos areas)

---

### Test Case 2: Existing User with Formal Override
```json
{
  "user_id": "user_042",
  "persona_text": "Formal English",
  "product_name": "Mama Cass",
  "product_category": "Nigerian Restaurant"
}
```

**Expected Output:**
- Review in formal English
- Professional tone
- Still includes Nigerian cultural references

---

### Test Case 3: Cold Start User
```json
{
  "user_id": "cold_start",
  "persona_text": "I'm a Gen Z foodie who loves trying new restaurants in Lagos. I prefer casual vibes and Instagram-worthy spots.",
  "product_name": "Cafe Neo",
  "product_category": "Coffee Shop"
}
```

**Expected Output:**
- Review matching the Gen Z persona
- Casual, trendy language
- Focus on aesthetics and vibes

---

## Task B: Get Recommendations

### Test Case 1: History-Based Recommendations
```json
{
  "user_id": "user_001",
  "persona_text": "I want something similar to what I usually like",
  "top_k": 5
}
```

**Expected Output:**
- 5 recommendations based on user's review history
- Diverse categories (cross-domain expansion)
- Nigerian restaurant names and locations
- Mode: "history_based"

---

### Test Case 2: Cold-Start with Specific Preferences
```json
{
  "user_id": "cold_start",
  "persona_text": "I want affordable Nigerian food in Surulere",
  "top_k": 3
}
```

**Expected Output:**
- 3 recommendations matching the query
- Nigerian restaurants in Surulere area
- Budget-friendly options
- Mode: "cold_start"

**Important:** For cold-start, always use `user_id="cold_start"`

---

### Test Case 3: Cold-Start with Different Preferences
```json
{
  "user_id": "cold_start",
  "persona_text": "Looking for upscale dining and cocktails in Victoria Island for a date night",
  "top_k": 5
}
```

**Expected Output:**
- 5 upscale restaurants/bars
- Victoria Island locations
- Romantic/date-night vibes
- Mode: "cold_start"

---

### Test Case 4: Testing top_k Parameter
```json
{
  "user_id": "cold_start",
  "persona_text": "I want good coffee shops in Lekki",
  "top_k": 7
}
```

**Expected Output:**
- Exactly 7 recommendations (not 5 or 10)
- Coffee shops in Lekki area
- Mode: "cold_start"

---

## Using curl Commands

### Task A - Generate Review
```bash
curl -X POST "http://localhost:8000/generate-review" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "persona_text": "Pidgin Pro",
    "product_name": "Chicken Republic",
    "product_category": "Fast Food"
  }'
```

### Task B - Get Recommendations (History-Based)
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "persona_text": "Similar to what I like",
    "top_k": 5
  }'
```

### Task B - Get Recommendations (Cold-Start)
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "cold_start",
    "persona_text": "I want affordable Nigerian food in Surulere",
    "top_k": 3
  }'
```

---

## Get Demo Users

```bash
curl -X GET "http://localhost:8000/demo-users"
```

**Returns:**
```json
[
  {
    "user_id": "user_001",
    "display_name": "The Lagos Foodie",
    "description": "Loves trying new restaurants, writes detailed reviews"
  },
  {
    "user_id": "user_042",
    "display_name": "The Budget King",
    "description": "Always looking for affordable options, harsh critic"
  }
]
```

---

