# Image Loading Indicator - Visual Feedback

## Overview

Added a visual loading indicator that shows a placeholder with a spinner while images are being generated. This provides clear feedback to users that image generation is in progress.

## Features

### ✅ Loading Placeholder

**Visual elements:**
- 512×512px dashed border frame
- Animated spinner icon
- Status message ("Generating image..." or "Refining image...")
- Semi-transparent background
- Responsive design

### ✅ Smart Detection

**Shows placeholder when:**
- Message contains "🎨 Generating image"
- Message contains "🔄 Refining previous image"
- No images in `meta_data` yet (still generating)

**Hides placeholder when:**
- Image generation completes
- Images appear in `meta_data`

### ✅ Context-Aware Messages

**Different messages for different scenarios:**
- "Generating image..." - New image from text
- "Refining image..." - Multi-turn editing

## Implementation

### New Component: ImageLoadingPlaceholder

**Location:** `frontend/src/components/ImageLoadingPlaceholder.jsx`

```jsx
import { Loader2 } from 'lucide-react'

export default function ImageLoadingPlaceholder({ message = "Generating image..." }) {
  return (
    <div className="relative inline-block my-4">
      <div 
        className="flex items-center justify-center bg-secondary/50 border-2 border-dashed border-border rounded-lg"
        style={{
          width: '512px',
          height: '512px',
          maxWidth: '100%'
        }}
      >
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Loader2 size={48} className="animate-spin" />
          <p className="text-sm font-medium">{message}</p>
        </div>
      </div>
    </div>
  )
}
```

### ChatMessage Integration

**Detection logic:**
```jsx
const isGeneratingImage = !isUser && 
  (message.content.includes('🎨 Generating image') || 
   message.content.includes('🔄 Refining previous image')) &&
  (!message.meta_data?.images || message.meta_data.images.length === 0)
```

**Rendering:**
```jsx
{/* Display loading placeholder for image generation */}
{isGeneratingImage && (
  <ImageLoadingPlaceholder 
    message={message.content.includes('🔄 Refining') ? "Refining image..." : "Generating image..."}
  />
)}

{/* Display images when ready */}
{message.meta_data?.images && message.meta_data.images.length > 0 && (
  <div className="flex flex-wrap gap-2 mb-3">
    {message.meta_data.images.map((img, idx) => (
      <MarkdownImage key={idx} src={img} alt={`Generated ${idx + 1}`} />
    ))}
  </div>
)}
```

## Visual Design

### Placeholder Appearance

```
┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                                             │
│                                             │
│                                             │
│                  ⟳                          │  ← Spinning icon
│                                             │
│           Generating image...               │  ← Status text
│                                             │
│                                             │
│                                             │
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

**Styling:**
- Dashed border (2px)
- Semi-transparent background
- Centered content
- Smooth animations
- Responsive sizing

### Animation

**Spinner:**
- Continuous rotation
- 48px size
- Smooth animation
- Muted color

**Transition:**
```
Loading placeholder visible
    ↓
Image generation completes
    ↓
Placeholder disappears
    ↓
Actual image appears
```

## User Experience

### Flow Example

**1. User sends prompt:**
```
User: "A mountain landscape"
```

**2. Placeholder appears immediately:**
```
Assistant: 🎨 Generating image with gpt-image-1...

┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│           ⟳                       │
│    Generating image...            │
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

**3. Image completes:**
```
Assistant: 🎨 Generated image using gpt-image-1

[Actual mountain image displayed]
```

### Multi-Turn Example

**1. User refines:**
```
User: "Add a sunset"
```

**2. Refining placeholder:**
```
Assistant: 🔄 Refining previous image...

┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│           ⟳                       │
│     Refining image...             │
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

**3. Refined image appears:**
```
Assistant: 🎨 Generated image using gpt-image-1

[Mountain with sunset displayed]
```

## Benefits

### For Users

✅ **Clear feedback** - Know generation is happening
✅ **Visual consistency** - Placeholder matches final image size
✅ **Reduced anxiety** - No blank waiting period
✅ **Professional feel** - Polished loading state

### For UX

✅ **Perceived performance** - Feels faster with feedback
✅ **Space reservation** - No layout shift when image loads
✅ **Context awareness** - Different messages for different actions
✅ **Smooth transitions** - Placeholder → Image

## Technical Details

### Detection Logic

**Checks three conditions:**
1. Message is from assistant (not user)
2. Content includes generation keywords
3. No images in meta_data yet

**Keywords:**
- "🎨 Generating image"
- "🔄 Refining previous image"

### Responsive Behavior

**Desktop:**
- 512×512px placeholder
- Full size display

**Mobile:**
- max-width: 100%
- Scales down proportionally
- Maintains aspect ratio

### Performance

**Lightweight:**
- Single component
- No heavy dependencies
- CSS animations only
- Fast rendering

## Testing

### Test 1: New Image Generation

1. Select "GPT-Image-1"
2. Type: `"A red apple"`
3. Send
4. **Verify:**
   - ✅ Placeholder appears immediately
   - ✅ Shows "Generating image..."
   - ✅ Spinner animates
   - ✅ Placeholder disappears when image loads
   - ✅ Image displays correctly

### Test 2: Multi-Turn Refinement

1. Generate an image
2. Type: `"Make it green"`
3. Send
4. **Verify:**
   - ✅ Placeholder appears
   - ✅ Shows "Refining image..."
   - ✅ Spinner animates
   - ✅ Transitions to refined image

### Test 3: Streaming Mode

1. Enable streaming
2. Generate image
3. **Verify:**
   - ✅ Placeholder shows during generation
   - ✅ Updates when image ready
   - ✅ Smooth transition

### Test 4: Error Handling

1. Generate with invalid prompt
2. **Verify:**
   - ✅ Placeholder shows
   - ✅ Error message appears
   - ✅ No broken state

## Comparison

### Before (No Indicator)

```
User: "Generate an image"
Assistant: 🎨 Generating image with gpt-image-1...
[Blank space]
[Wait...]
[Wait...]
[Image suddenly appears]
```
❌ No feedback during generation
❌ Layout shift when image loads
❌ User unsure if it's working

### After (With Indicator)

```
User: "Generate an image"
Assistant: 🎨 Generating image with gpt-image-1...
[Placeholder with spinner appears]
[Generating...]
[Smooth transition to image]
```
✅ Clear visual feedback
✅ No layout shift
✅ Professional experience

## Customization

### Change Placeholder Size

```jsx
<div style={{
  width: '768px',  // Larger
  height: '768px',
  maxWidth: '100%'
}}>
```

### Change Message

```jsx
<ImageLoadingPlaceholder 
  message="Creating your masterpiece..."
/>
```

### Change Spinner Size

```jsx
<Loader2 size={64} className="animate-spin" />
```

### Change Colors

```jsx
<div className="bg-primary/10 border-primary">
  {/* ... */}
</div>
```

## Summary

### What Was Added

✅ **ImageLoadingPlaceholder component** - Reusable loading state
✅ **Smart detection** - Shows when generating
✅ **Context-aware messages** - Different text for different actions
✅ **Smooth transitions** - Placeholder → Image
✅ **Responsive design** - Works on all screen sizes

### How It Works

1. **User sends prompt** for image generation
2. **Placeholder appears** immediately with spinner
3. **Backend generates** image
4. **Placeholder disappears** when image ready
5. **Actual image displays** in same position

### Benefits

✅ **Better UX** - Clear feedback during generation
✅ **Professional** - Polished loading state
✅ **No layout shift** - Space reserved
✅ **Context-aware** - Appropriate messages

---

**Status**: ✅ Implemented
**Component**: `ImageLoadingPlaceholder.jsx`
**Integration**: `ChatMessage.jsx`
**Testing**: Ready for testing
