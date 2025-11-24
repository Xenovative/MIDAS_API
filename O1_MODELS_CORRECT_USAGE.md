# O1 Models - Correct Usage (Per OpenAI Docs)

## Critical Information

**O1 models (o1-preview, o1-mini) only support MINIMAL parameters:**

### ✅ Supported Parameters
- `model` - The model name
- `messages` - The conversation messages

### ❌ NOT Supported Parameters
- `temperature` - O1 uses fixed temperature
- `max_tokens` - Not supported
- `max_completion_tokens` - Not supported
- `top_p` - Not supported
- `frequency_penalty` - Not supported
- `presence_penalty` - Not supported
- `reasoning_effort` - Not in current SDK
- `system` role - Use `user` role only

## Correct API Call

```python
# ✅ CORRECT - Minimal parameters only
response = await client.chat.completions.create(
    model="o1-preview",
    messages=[
        {"role": "user", "content": "Your question here"}
    ]
)
```

```python
# ❌ WRONG - These will cause errors
response = await client.chat.completions.create(
    model="o1-preview",
    messages=[...],
    temperature=0.7,  # ERROR!
    max_tokens=1000,  # ERROR!
    max_completion_tokens=1000,  # ERROR!
    reasoning_effort="high"  # ERROR!
)
```

## Why O1 Models Are Different

**O1 models have fixed, optimized settings:**
- They automatically determine optimal token usage
- They use internal reasoning with chain-of-thought
- Temperature and other parameters are pre-configured
- You cannot override these settings

**This is by design:**
- O1 models are reasoning models, not chat models
- They need specific settings for optimal reasoning
- OpenAI controls these settings for best results

## Implementation

### Our chat_with_reasoning Method

```python
async def chat_with_reasoning(
    messages: List[Dict[str, str]],
    model: str,
    reasoning_effort: str = "medium",  # Ignored
    max_completion_tokens: Optional[int] = None  # Ignored
) -> Dict[str, Any]:
    """
    O1 models only accept model and messages
    All other parameters are ignored
    """
    params = {
        "model": model,
        "messages": messages,
    }
    
    response = await client.chat.completions.create(**params)
    return response
```

### Deep Research RAG

```python
if is_reasoning_model:
    # O1 models - minimal parameters only
    response = await provider.chat_with_reasoning(
        messages=messages,
        model=model_name
        # No other parameters!
    )
else:
    # GPT-4 models - full parameters
    response = await provider.chat(
        messages=messages,
        model=model_name,
        temperature=0.3,
        max_tokens=10000
    )
```

## Console Output

### O1 Model Call

```
🔬 Attempting deep research with o1-preview...
📊 Analyzing 15 document sections
   → Using O1/O3 reasoning model (fixed settings)
   → O1 models control their own token usage
🔬 Calling O1/O3 model: o1-preview
   → Using minimal parameters (O1 models have fixed settings)
✅ Deep research complete with o1-preview (8432 tokens)
```

### GPT-4 Fallback

```
🔬 Attempting deep research with gpt-4o...
   → Using GPT-4 parameters (temperature: 0.3)
   → max_tokens: 10000
✅ Deep research complete with gpt-4o (2847 tokens)
```

## Model Comparison

### O1 Models

**Parameters:**
```python
{
    "model": "o1-preview",
    "messages": [...]
}
```

**Characteristics:**
- Fixed settings (optimized by OpenAI)
- Automatic token management
- Deep reasoning built-in
- Cannot customize behavior

### GPT-4 Models

**Parameters:**
```python
{
    "model": "gpt-4o",
    "messages": [...],
    "temperature": 0.3,
    "max_tokens": 10000,
    "top_p": 1.0,
    # ... many more options
}
```

**Characteristics:**
- Fully customizable
- Manual token limits
- Adjustable temperature
- Flexible behavior

## Cost Implications

### O1 Models

**You cannot control token usage:**
- O1 decides how many tokens to use
- Can use 5,000-25,000+ tokens per query
- Cost varies significantly per query
- No way to limit this

**Pricing:**
- o1-preview: $15 input / $60 output per 1M tokens
- o1-mini: $3 input / $12 output per 1M tokens

**Example costs:**
- Simple query: $0.50-2.00
- Complex query: $2.00-10.00
- Very complex: $10.00-50.00

### GPT-4 Models

**You can control token usage:**
- Set max_tokens to limit cost
- Predictable pricing
- Budget-friendly

**Pricing:**
- gpt-4o: $2.50 input / $10 output per 1M tokens

**Example costs:**
- With max_tokens=1000: $0.05-0.15
- With max_tokens=4000: $0.15-0.50

## Fallback Strategy

### Current Implementation

```
1. Try o1-preview (if available)
   - Minimal parameters only
   - Let O1 control everything
   
2. If unavailable → Try o1-mini
   - Minimal parameters only
   
3. If unavailable → Use gpt-4o
   - Full parameters
   - Controlled token usage
   - Always works
```

### Why This Works

- O1 models provide best reasoning (when available)
- GPT-4o provides reliable fallback (always available)
- No errors from unsupported parameters
- Graceful degradation

## Testing

### Test O1 Model

**1. Enable Deep Research toggle**

**2. Ask complex question:**
```
"Analyze the fundamental differences between quantum 
mechanics and general relativity"
```

**3. Check console:**
```
🔬 Attempting deep research with o1-preview...
   → Using O1/O3 reasoning model (fixed settings)
   → O1 models control their own token usage
🔬 Calling O1/O3 model: o1-preview
   → Using minimal parameters
✅ Deep research complete with o1-preview
```

**4. Verify:**
- No parameter errors
- Deep reasoning in response
- High token usage (normal for O1)

### Test Fallback

**If O1 not available:**
```
⚠️  Error with o1-preview: model not found
   → Model not available, trying next model...
🔬 Attempting deep research with gpt-4o...
   → Using GPT-4 parameters (temperature: 0.3)
✅ Deep research complete with gpt-4o
```

## Summary

### Key Points

✅ **O1 models use minimal parameters** - only model and messages
✅ **No token limits** - O1 controls its own usage
✅ **No temperature** - O1 uses fixed settings
✅ **Deep reasoning built-in** - no special parameters needed
✅ **Automatic fallback** - to GPT-4o if O1 unavailable

### What NOT to Do

❌ Don't pass `temperature` to O1
❌ Don't pass `max_tokens` to O1
❌ Don't pass `max_completion_tokens` to O1
❌ Don't pass `reasoning_effort` (not in SDK yet)
❌ Don't try to control O1's behavior

### What TO Do

✅ Use minimal parameters (model + messages)
✅ Let O1 control its own settings
✅ Have GPT-4o as fallback
✅ Monitor token usage (can be high)
✅ Budget accordingly for O1 costs

---

**Status**: ✅ Implemented correctly
**Parameters**: Minimal (model + messages only)
**Fallback**: Automatic to GPT-4o
**Cost**: Variable (O1 controls usage)
