# Blurred Previous Image in Loading Placeholder

## Overview

Enhanced the image loading placeholder to show a blurred version of the previous image when doing multi-turn refinement. This provides visual context and continuity during the refinement process.

## Features

### ✅ Context-Aware Display

**New image generation:**
```
┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                                   │
│            ⟳                      │
│     Generating image...           │
│                                   │
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

**Multi-turn refinement:**
```
┌───────────────────────────────────┐
│  [Blurred previous image]         │
│                                   │
│     ┌─────────────────┐           │
│     │       ⟳         │           │
│     │ Refining image...│          │
│     └─────────────────┘           │
│                                   │
└───────────────────────────────────┘
```

### ✅ Visual Effects

**Blurred background:**
- 8px blur filter
- 40% opacity
- Covers entire placeholder
- Maintains aspect ratio

**Loading overlay:**
- Semi-transparent background (80%)
- Backdrop blur effect
- Elevated with shadow
- Centered content

## Implementation

### ImageLoadingPlaceholder Component

**Updated component:**
```jsx
export default function ImageLoadingPlaceholder({ 
  message = "Generating image...",
  previousImage = null 
}) {
  return (
    <div className="relative inline-block my-4">
      <div className="relative flex items-center justify-center bg-secondary/50 border-2 border-dashed border-border rounded-lg overflow-hidden">
        
        {/* Previous image with blur effect */}
        {previousImage && (
          <img
            src={previousImage}
            alt="Previous"
            className="absolute inset-0 w-full h-full object-cover"
            style={{
              filter: 'blur(8px)',
              opacity: 0.4
            }}
          />
        )}
        
        {/* Loading overlay */}
        <div className="relative z-10 flex flex-col items-center gap-3 text-foreground bg-background/80 backdrop-blur-sm px-6 py-4 rounded-lg shadow-lg">
          <Loader2 size={48} className="animate-spin" />
          <p className="text-sm font-medium">{message}</p>
        </div>
      </div>
    </div>
  )
}
```

### ChatMessage Integration

**Extract previous image:**
```jsx
// Get previous image for multi-turn refinement
const previousImage = previousAssistantMessage?.meta_data?.images?.[0] || null
```

**Pass to placeholder:**
```jsx
{isGeneratingImage && (
  <ImageLoadingPlaceholder 
    message={message.content.includes('🔄 Refining') ? "Refining image..." : "Generating image..."}
    previousImage={message.content.includes('🔄 Refining') ? previousImage : null}
  />
)}
```

### ChatArea Integration

**Find previous assistant message:**
```jsx
let previousAssistantMessage = null

if (message.role === 'assistant') {
  // Find previous assistant message (for multi-turn image refinement)
  for (let i = index - 1; i >= 0; i--) {
    if (currentConversation.messages[i].role === 'assistant') {
      previousAssistantMessage = currentConversation.messages[i]
      break
    }
  }
}
```

**Pass to ChatMessage:**
```jsx
<ChatMessage 
  message={message}
  previousUserMessage={previousUserMessage}
  previousAssistantMessage={previousAssistantMessage}
/>
```

## User Experience

### Example Flow

**Turn 1: Generate base image**
```
User: "A mountain landscape"
