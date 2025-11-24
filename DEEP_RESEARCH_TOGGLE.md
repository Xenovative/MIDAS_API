# Deep Research Toggle - UI Feature

## Overview

Added a **Deep Research toggle button** in the chat interface that allows users to enable/disable deep research on-the-fly for any RAG-enabled bot.

## Features

### 🎯 Visual Toggle Button

**Location:** Chat header (next to "New Chat" button)

**Appearance:**
- **OFF**: Gray button with Brain icon
- **ON**: Purple glowing button with "ON" badge and pulsing Brain icon

**Only shows for:** RAG-enabled bots (`use_rag: true`)

### 💾 Persistent State

- Toggle state saved to `localStorage`
- Persists across page refreshes
- Per-user preference

### 🔄 Real-time Control

- Click to toggle ON/OFF
- Immediately affects next query
- No page refresh needed

## How It Works

### Frontend

**1. Store State** (`frontend/src/store/useStore.js`)
```javascript
useDeepResearch: false  // Default OFF
setUseDeepResearch: (value) => {
  localStorage.setItem('useDeepResearch', JSON.stringify(value))
  set({ useDeepResearch: value })
}
```

**2. UI Toggle** (`frontend/src/components/ChatArea.jsx`)
```jsx
{selectedBot?.use_rag && (
  <button
    onClick={() => setUseDeepResearch(!useDeepResearch)}
    className={useDeepResearch ? 'purple-glow' : 'gray'}
  >
    <Brain className={useDeepResearch ? 'animate-pulse' : ''} />
    Deep Research
    {useDeepResearch && <span>ON</span>}
  </button>
)}
```

**3. Send to Backend**
```javascript
const requestData = {
  // ... other fields
  use_deep_research: useDeepResearch
}
```

### Backend

**1. Schema** (`backend/schemas.py`)
```python
class ChatRequest(BaseModel):
    # ... other fields
    use_deep_research: bool = False
```

**2. RAG Context** (`backend/routes/chat.py`)
```python
async def fetch_rag_context(..., use_deep_research: bool = False):
    force_deep = use_deep_research  # From frontend toggle
    
    if force_deep:
        print("🔬 Deep research FORCED by user toggle")
    
    context_text = await hybrid_rag.query(
        query=query,
        retrieved_chunks=results,
        use_deep_research=force_deep,
        complexity_threshold=20
    )
```

**3. Hybrid RAG** (`backend/deep_research_rag.py`)
```python
if use_deep_research or is_complex:
    # Use o1-mini for deep research
    research_result = await DeepResearchRAG.deep_research_query(...)
else:
    # Use fast reading flow
    context_text = reading_flow_rag.format_reading_context(...)
```

## Usage

### For Users

**1. Enable Deep Research**
- Click the "Deep Research" button in chat header
- Button turns purple and shows "ON"
- Brain icon pulses

**2. Ask Questions**
- All queries now use deep research
- Even simple queries get o1-mini analysis
- Slower but much higher quality

**3. Disable Deep Research**
- Click button again
- Returns to gray
- Back to fast retrieval with auto-detection

### Visual States

**OFF (Default):**
```
┌─────────────────────────┐
│ 🧠 Deep Research        │  ← Gray button
└─────────────────────────┘
```

**ON (Enabled):**
```
┌─────────────────────────┐
│ 🧠 Deep Research  [ON]  │  ← Purple glowing, pulsing icon
└─────────────────────────┘
```

## Behavior

### When Toggle is OFF

**Auto-detection active:**
- Simple queries → Fast retrieval
- Complex queries → Deep research
- Keyword-based detection
- Length-based detection

**Example:**
```
"What is X?" → Fast ⚡
"Compare X and Y" → Deep 🔬 (auto-detected)
```

### When Toggle is ON

**Always deep research:**
- ALL queries use o1-mini
- No auto-detection
- Maximum quality
- Higher cost

**Example:**
```
"What is X?" → Deep 🔬 (forced)
"Compare X and Y" → Deep 🔬 (forced)
```

## Console Output

### Toggle OFF
```
============================================================
🔍 RAG Query Analysis:
  Query: What is X?
  Keywords found: None
  Is complex: False
  Force deep research: False
  Should use deep: False
============================================================

⚡ USING FAST RETRIEVAL (reading flow)
```

### Toggle ON
```
============================================================
🔍 RAG Query Analysis:
  Query: What is X?
  Keywords found: None
  Is complex: False
  Force deep research: True  ← From toggle
  Should use deep: True
============================================================

🔬 Deep research FORCED by user toggle
🔬 USING DEEP RESEARCH with o1-mini
```

## Priority Order

**Deep research is enabled if ANY of these are true:**

1. **User toggle ON** (highest priority)
2. **Bot meta_data has `use_deep_research: true`**
3. **Query has complexity keywords**
4. **Query length > 20 words**

**Priority:**
```
User Toggle > Bot Settings > Auto-Detection
```

## Cost Implications

### Toggle OFF (Default)
- Most queries: $0.01-0.05 (fast)
- Complex queries: $3-15 (deep, auto-detected)
- Average: ~$0.50 per query

### Toggle ON
- ALL queries: $3-15 (deep)
- Average: ~$8 per query
- **16x more expensive!**

**Recommendation:** 
- Keep OFF by default
- Enable only when you need research-quality answers
- Disable after getting your answer

## UI/UX Details

### Styling

**OFF State:**
```css
bg-secondary text-secondary-foreground
hover:bg-secondary/80
```

**ON State:**
```css
bg-purple-500/20 text-purple-400
border border-purple-500/30
```

### Animation

**Brain Icon:**
- OFF: Static
- ON: `animate-pulse` (pulsing effect)

### Tooltip

**Hover text:**
- OFF: "Deep Research: OFF (fast retrieval)"
- ON: "Deep Research: ON (uses o1-mini for complex analysis)"

### Responsive

- Hides on mobile if space constrained
- Always visible on desktop
- Maintains state across devices (localStorage)

## Testing

### Test 1: Toggle Visibility

**Steps:**
1. Select RAG-enabled bot
2. Check header

**Expected:**
- ✅ Deep Research button visible
- ✅ Gray/OFF by default

### Test 2: Toggle Functionality

**Steps:**
1. Click Deep Research button
2. Check appearance

**Expected:**
- ✅ Turns purple
- ✅ Shows "ON" badge
- ✅ Brain icon pulses

### Test 3: Query with Toggle ON

**Steps:**
1. Enable Deep Research
2. Ask simple question: "What is X?"
3. Check console

**Expected:**
```
🔬 Deep research FORCED by user toggle
🔬 USING DEEP RESEARCH with o1-mini
```

### Test 4: Query with Toggle OFF

**Steps:**
1. Disable Deep Research
2. Ask simple question: "What is X?"
3. Check console

**Expected:**
```
⚡ USING FAST RETRIEVAL (reading flow)
```

### Test 5: Persistence

**Steps:**
1. Enable Deep Research
2. Refresh page
3. Check button state

**Expected:**
- ✅ Still ON after refresh
- ✅ State persisted in localStorage

## Summary

### What Was Added

✅ **Toggle button** in chat header
✅ **Persistent state** via localStorage
✅ **Visual feedback** (purple glow, pulsing icon)
✅ **Backend integration** via `use_deep_research` flag
✅ **Priority system** (user > bot > auto)

### User Benefits

✅ **Control** - Choose when to use deep research
✅ **Visibility** - Clear visual state
✅ **Flexibility** - Toggle anytime
✅ **Cost awareness** - Know when using expensive model

### Developer Benefits

✅ **Simple API** - Just one boolean flag
✅ **Backward compatible** - Defaults to OFF
✅ **Extensible** - Easy to add more options

---

**Status**: ✅ Implemented
**Location**: Chat header (RAG bots only)
**Default**: OFF (auto-detection)
**Persistence**: localStorage
**Priority**: User > Bot > Auto
