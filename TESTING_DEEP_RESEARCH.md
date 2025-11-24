# Testing Deep Research RAG

## How to See Deep Research in Action

### Method 1: Use Complexity Keywords

**Ask questions with these keywords:**
- "analyze"
- "compare"
- "explain"
- "why"
- "how"
- "relationship"
- "difference"
- "similarity"
- "comprehensive"
- "detailed"
- "thorough"

**Examples:**
```
✅ "Compare approach A and B"
✅ "Analyze the relationship between X and Y"
✅ "Explain why this happens"
✅ "How does X differ from Y?"
✅ "What is the difference between..."
```

### Method 2: Ask Long Questions

**Questions > 20 words trigger deep research:**

```
✅ "What are the main differences between quantum mechanics 
    and classical mechanics, and how do they apply to 
    different scales of observation?"
    
✅ "Can you provide a comprehensive analysis of the 
    advantages and disadvantages of each approach 
    mentioned in the document?"
```

### Method 3: Enable Deep Research in Bot Settings

**For always-on deep research:**

1. Go to Bot Manager
2. Edit your bot
3. Add to bot's meta_data:
   ```json
   {
     "use_deep_research": true
   }
   ```
4. Save bot

Now ALL queries to that bot will use deep research!

## What to Look For

### In Backend Console

**When deep research is used:**
```
============================================================
🔍 RAG Query Analysis:
  Query: Compare approach A and B...
  Query length: 5 words
  Complexity threshold: 20 words
  Keywords found: ['compare']
  Is complex: True
  Force deep research: False
  Should use deep: True
  Retrieved chunks: 5
============================================================

🔬 USING DEEP RESEARCH with o1-mini
🔬 Starting deep research with o1-mini...
📊 Analyzing 5 document sections
✅ Deep research complete (8432 reasoning tokens)
```

**When fast retrieval is used:**
```
============================================================
🔍 RAG Query Analysis:
  Query: What is X?...
  Query length: 3 words
  Complexity threshold: 20 words
  Keywords found: None
  Is complex: False
  Force deep research: False
  Should use deep: False
  Retrieved chunks: 5
============================================================

⚡ USING FAST RETRIEVAL (reading flow)
```

### In Chat Response

**Deep Research Response:**
```
=== DEEP RESEARCH ANALYSIS ===

Analysis performed by: o1-mini
Reasoning tokens used: 8,432

============================================================
RESEARCH FINDINGS:
============================================================

[Comprehensive, well-reasoned answer with citations]
```

**Fast Retrieval Response:**
```
=== DOCUMENT READING CONTEXT ===

📖 Reading from: document.pdf

[Formatted chunks in reading order]
```

## Testing Checklist

### ✅ Test 1: Simple Query (Should use fast retrieval)

**Query:** "What is quantum mechanics?"

**Expected:**
- Console shows: `⚡ USING FAST RETRIEVAL`
- Response has: `=== DOCUMENT READING CONTEXT ===`
- Fast response (< 1 second)

### ✅ Test 2: Complex Query with Keyword (Should use deep research)

**Query:** "Compare quantum mechanics and classical mechanics"

**Expected:**
- Console shows: `🔬 USING DEEP RESEARCH`
- Console shows: `Keywords found: ['compare']`
- Response has: `=== DEEP RESEARCH ANALYSIS ===`
- Slower response (5-15 seconds)
- Reasoning tokens shown

### ✅ Test 3: Long Query (Should use deep research)

**Query:** "What are the main principles of quantum mechanics and how do they differ from classical mechanics in terms of their fundamental assumptions and practical applications?"

**Expected:**
- Console shows: `🔬 USING DEEP RESEARCH`
- Console shows: `Query length: 26 words` (> 20 threshold)
- Response has: `=== DEEP RESEARCH ANALYSIS ===`

### ✅ Test 4: Force Deep Research via Bot

**Setup:**
1. Edit bot meta_data: `{"use_deep_research": true}`
2. Ask simple question: "What is X?"

**Expected:**
- Console shows: `🔬 Bot has deep research enabled`
- Console shows: `Force deep research: True`
- Console shows: `🔬 USING DEEP RESEARCH`
- Even simple queries use deep research

## Troubleshooting

### Issue 1: Always Using Fast Retrieval

**Symptoms:**
- Console always shows `⚡ USING FAST RETRIEVAL`
- Never see deep research

**Solutions:**
1. **Use complexity keywords:**
   - Try: "Compare X and Y"
   - Try: "Analyze the relationship"
   
2. **Ask longer questions:**
   - Make query > 20 words
   
3. **Force deep research:**
   - Enable in bot settings
   - Or lower threshold in code

### Issue 2: Deep Research Not Working

**Symptoms:**
- Console shows `🔬 USING DEEP RESEARCH`
- But error occurs

**Check:**
1. **OpenAI API key** - Must be valid
2. **Model access** - Must have access to o1-mini
3. **Console errors** - Look for error messages

**Common errors:**
```
❌ Model 'o1-mini' not found
→ Check OpenAI account has access

❌ Rate limit exceeded
→ Wait and try again

❌ Insufficient quota
→ Add credits to OpenAI account
```

### Issue 3: Too Expensive

**Symptoms:**
- Deep research working but costs too much

**Solutions:**
1. **Increase threshold:**
   ```python
   complexity_threshold=50  # Higher = less deep research
   ```

2. **Disable auto-detection:**
   ```python
   use_deep_research=False
   complexity_threshold=999999  # Never auto-trigger
   ```

3. **Use only when needed:**
   - Only enable for specific bots
   - Only use for important queries

## Current Settings

**Default Configuration:**
```python
# In backend/routes/chat.py
complexity_threshold=20  # Words (lower = more aggressive)

# In backend/deep_research_rag.py
reasoning_model="o1-mini"  # Fast, cost-effective
max_reasoning_tokens=10000  # Max tokens for reasoning
```

**Complexity Keywords:**
```python
[
    'analyze', 'compare', 'explain', 'why', 'how',
    'relationship', 'difference', 'similarity',
    'comprehensive', 'detailed', 'thorough'
]
```

## Quick Test Commands

**Copy-paste these to test:**

```
# Test 1: Simple (should be fast)
What is quantum mechanics?

# Test 2: Compare (should be deep)
Compare quantum mechanics and classical mechanics

# Test 3: Analyze (should be deep)
Analyze the relationship between X and Y

# Test 4: Explain (should be deep)
Explain why this approach is better

# Test 5: Long (should be deep)
What are the main differences between approach A and approach B, and what are the advantages and disadvantages of each in practical applications?
```

## Summary

### To See Deep Research:

✅ **Use keywords**: compare, analyze, explain, why, how
✅ **Ask long questions**: > 20 words
✅ **Enable in bot**: Add `use_deep_research: true` to bot meta_data

### To Verify It's Working:

✅ **Check console**: Look for `🔬 USING DEEP RESEARCH`
✅ **Check response**: Look for `=== DEEP RESEARCH ANALYSIS ===`
✅ **Check timing**: Deep research takes 5-15 seconds
✅ **Check tokens**: Should show reasoning tokens used

---

**Status**: ✅ Ready to test
**Threshold**: 20 words (aggressive)
**Keywords**: 10 complexity keywords
**Default Model**: o1-mini
