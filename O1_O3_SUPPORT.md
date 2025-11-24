# O1 Pro & O3 Support - Intelligent Model Fallback

## Overview

Deep Research now supports **o1-pro**, **o1-preview**, **o1-mini**, and **o3-mini** with **automatic fallback** to available models!

## How It Works

### Intelligent Fallback Chain

When you request a model, the system tries models in order until one works:

```
"o1" → o1-pro → o1-preview → o1-mini → gpt-4o
"o3" → o3-mini → o1-mini → gpt-4o
```

**Example:**
```
🔄 Model fallback chain: o1-pro → o1-preview → o1-mini → gpt-4o
🔬 Attempting deep research with o1-pro...
⚠️  o1-pro not available, trying next model...
🔬 Attempting deep research with o1-preview...
⚠️  o1-preview not available, trying next model...
🔬 Attempting deep research with o1-mini...
⚠️  o1-mini not available, trying next model...
🔬 Attempting deep research with gpt-4o...
✅ Deep research complete with gpt-4o (2847 tokens)
```

## Supported Models

### O1 Family (Reasoning Models)

**1. o1-pro** (Best)
- Most advanced reasoning
- Highest quality analysis
- Requires special access
- ~$15 per 1M input tokens

**2. o1-preview**
- Advanced reasoning
- High quality
- Limited availability
- ~$15 per 1M input tokens

**3. o1-mini** (Fast)
- Good reasoning
- Cost-effective
- More widely available
- ~$3 per 1M input tokens

### O3 Family (Latest)

**o3-mini**
- Latest reasoning model
- Excellent performance
- Limited availability
- Pricing TBD

### GPT-4 Family (Fallback)

**gpt-4o** (Always Available)
- Excellent analysis
- Fast and reliable
- Available to all
- ~$2.50 per 1M input tokens

## Default Configuration

```python
# backend/deep_research_rag.py

reasoning_model = "o1"  # Default
# Tries: o1-pro → o1-preview → o1-mini → gpt-4o
```

## Model Selection

### Option 1: Use O1 Family (Recommended)

```python
reasoning_model = "o1"
# Automatically uses best available O1 model
```

**Fallback chain:**
1. o1-pro (if you have access)
2. o1-preview (if available)
3. o1-mini (if available)
4. gpt-4o (always works)

### Option 2: Use Specific O1 Model

```python
# Force o1-pro with fallback
reasoning_model = "o1-pro"
# Chain: o1-pro → o1-preview → o1-mini → gpt-4o

# Force o1-mini with fallback
reasoning_model = "o1-mini"
# Chain: o1-mini → gpt-4o
```

### Option 3: Use O3 Family

```python
reasoning_model = "o3"
# Chain: o3-mini → o1-mini → gpt-4o
```

### Option 4: Use GPT-4 Only

```python
reasoning_model = "gpt-4o"
# No fallback, uses gpt-4o directly
```

## Console Output

### Successful Fallback

```
============================================================
🔍 RAG Query Analysis:
  Query: Compare X and Y...
  Keywords found: ['compare']
  Should use deep: True
============================================================

🔬 USING DEEP RESEARCH
🔄 Model fallback chain: o1-pro → o1-preview → o1-mini → gpt-4o
🔬 Attempting deep research with o1-pro...
⚠️  o1-pro not available, trying next model...
🔬 Attempting deep research with o1-preview...
⚠️  o1-preview not available, trying next model...
🔬 Attempting deep research with o1-mini...
⚠️  o1-mini not available, trying next model...
🔬 Attempting deep research with gpt-4o...
📊 Analyzing 5 document sections
✅ Deep research complete with gpt-4o (2847 tokens)
```

### With O1 Access

```
🔄 Model fallback chain: o1-pro → o1-preview → o1-mini → gpt-4o
🔬 Attempting deep research with o1-pro...
📊 Analyzing 5 document sections
✅ Deep research complete with o1-pro (8432 tokens)
```

## Fallback Chains

### All Available Chains

| Requested | Fallback Chain |
|-----------|----------------|
| `o1` | o1-pro → o1-preview → o1-mini → gpt-4o |
| `o1-pro` | o1-pro → o1-preview → o1-mini → gpt-4o |
| `o1-preview` | o1-preview → o1-mini → gpt-4o |
| `o1-mini` | o1-mini → gpt-4o |
| `o3` | o3-mini → o1-mini → gpt-4o |
| `o3-mini` | o3-mini → o1-mini → gpt-4o |
| `gpt-4o` | gpt-4o |
| `gpt-4-turbo` | gpt-4-turbo → gpt-4o |
| `gpt-4o-mini` | gpt-4o-mini → gpt-4o |

## Model Comparison

### Reasoning Models (O1/O3)

**Characteristics:**
- Step-by-step reasoning
- Better at complex logic
- Slower but more thorough
- Fixed temperature (1.0)
- Higher token usage

**Best for:**
- Complex analysis
- Mathematical reasoning
- Multi-step problems
- Critical thinking tasks

### GPT-4 Models

**Characteristics:**
- Fast responses
- Good general analysis
- Adjustable temperature
- Lower token usage
- Always available

**Best for:**
- General questions
- Quick analysis
- When O1/O3 unavailable
- Cost-sensitive tasks

## Cost Comparison

### Per Query (5 chunks, 1000 tokens output)

| Model | Input | Output | Total |
|-------|-------|--------|-------|
| o1-pro | $0.075 | $0.60 | **$0.675** |
| o1-preview | $0.075 | $0.60 | **$0.675** |
| o1-mini | $0.015 | $0.06 | **$0.075** |
| o3-mini | TBD | TBD | **TBD** |
| gpt-4o | $0.0125 | $0.0375 | **$0.05** |

### Monthly (100 queries/day)

| Model | Daily | Monthly |
|-------|-------|---------|
| o1-pro | $67.50 | **$2,025** |
| o1-mini | $7.50 | **$225** |
| gpt-4o | $5.00 | **$150** |

## Configuration Options

### Environment Variable

**Add to `.env`:**
```bash
DEEP_RESEARCH_MODEL=o1
```

**Update code:**
```python
import os

reasoning_model = os.getenv("DEEP_RESEARCH_MODEL", "o1")
```

### Per-Bot Configuration

**In bot meta_data:**
```json
{
  "use_deep_research": true,
  "deep_research_model": "o1-pro"
}
```

**Update fetch_rag_context:**
```python
model = bot.meta_data.get('deep_research_model', 'o1')
research_result = await DeepResearchRAG.deep_research_query(
    query=query,
    retrieved_chunks=results,
    reasoning_model=model
)
```

### Per-Query Override

**In API request:**
```javascript
{
  use_deep_research: true,
  deep_research_model: "o1-pro"
}
```

## Testing

### Test Fallback Chain

**Ask a complex question with deep research ON:**
```
"Compare the advantages and disadvantages of approach A versus approach B"
```

**Watch console:**
```
🔄 Model fallback chain: o1-pro → o1-preview → o1-mini → gpt-4o
🔬 Attempting deep research with o1-pro...
[Shows which model actually works]
✅ Deep research complete with [model_name]
```

### Test Specific Model

**Edit `backend/deep_research_rag.py` line 310:**
```python
reasoning_model="o1-pro"  # Test specific model
```

**Restart and test**

## Recommendations

### For Most Users

```python
reasoning_model = "o1"  # Default
```

**Why:**
- Tries best models first
- Automatic fallback
- Always works
- Best quality available

### For O1 Pro Access

```python
reasoning_model = "o1-pro"
```

**Why:**
- Best reasoning quality
- Worth the cost for critical analysis
- Fallback if unavailable

### For Budget-Conscious

```python
reasoning_model = "o1-mini"
```

**Why:**
- Good reasoning
- 3x cheaper than o1-pro
- Falls back to gpt-4o

### For Speed

```python
reasoning_model = "gpt-4o"
```

**Why:**
- Fastest
- Cheapest
- No fallback needed
- Always available

## Summary

### What Changed

✅ **O1 Pro support** - Uses o1-pro if available
✅ **O3 support** - Uses o3-mini if available
✅ **Intelligent fallback** - Automatically tries models in order
✅ **No errors** - Always finds a working model
✅ **Transparent** - Shows which model is used

### Fallback Strategy

```
Request "o1" →
  Try o1-pro (best)
    ↓ Not available
  Try o1-preview
    ↓ Not available
  Try o1-mini
    ↓ Not available
  Use gpt-4o (always works)
```

### Benefits

✅ **Future-proof** - Supports new models as they release
✅ **Reliable** - Never fails due to missing model
✅ **Optimal** - Uses best available model
✅ **Transparent** - Shows fallback process
✅ **Flexible** - Easy to configure

---

**Status**: ✅ Implemented
**Default**: "o1" (tries o1-pro → o1-preview → o1-mini → gpt-4o)
**Fallback**: Automatic
**Models**: o1-pro, o1-preview, o1-mini, o3-mini, gpt-4o
