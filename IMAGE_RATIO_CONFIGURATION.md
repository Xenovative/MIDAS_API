# Image Ratio Configuration for GPT-Image-1

## Overview

Added a visual aspect ratio selector for GPT-Image-1 that allows users to choose different image dimensions and aspect ratios for image generation.

## Features

### ✅ Available Aspect Ratios

**Square (1:1)**
- Size: 1024x1024
- Icon: □
- Use case: Profile pictures, thumbnails, social media posts

**Landscape (16:9)**
- Size: 1792x1024
- Icon: ▭
- Use case: Widescreen displays, presentations, banners

**Portrait (9:16)**
- Size: 1024x1792
- Icon: ▯
- Use case: Mobile screens, stories, vertical content

**Standard (4:3)**
- Size: 1536x1152
- Icon: ▭
- Use case: Traditional displays, presentations

**Portrait (3:4)**
- Size: 1152x1536
- Icon: ▯
- Use case: Portrait photography, posters

## Implementation

### Frontend Components

**1. ImageRatioSelector Component**

```jsx
export default function ImageRatioSelector({ selectedRatio, onRatioChange, disabled = false }) {
  const ratios = [
    { id: '1:1', label: 'Square (1:1)', size: '1024x1024', icon: '□' },
    { id: '16:9', label: 'Landscape (16:9)', size: '1792x1024', icon: '▭' },
    { id: '9:16', label: 'Portrait (9:16)', size: '1024x1792', icon: '▯' },
    { id: '4:3', label: 'Standard (4:3)', size: '1536x1152', icon: '▭' },
    { id: '3:4', label: 'Portrait (3:4)', size: '1152x1536', icon: '▯' },
  ]
  
  return (
    <button onClick={() => setIsOpen(!isOpen)}>
      <AspectRatio size={16} />
      <span>{currentRatio.icon} {currentRatio.label}</span>
      <span>({currentRatio.size})</span>
    </button>
  )
}
```

**2. Store Integration**

```javascript
// State
imageRatio: '1:1',
imageSize: '1024x1024',

// Setter
setImageRatio: (ratio, size) => set({ imageRatio: ratio, imageSize: size })
```

**3. ChatArea Integration**

```jsx
{/* Image Ratio Selector - Show only for GPT-Image-1 */}
{selectedModel === 'gpt-image-1' && (
  <ImageRatioSelector
    selectedRatio={imageRatio}
    onRatioChange={setImageRatio}
  />
)}
```

### Backend Changes

**1. Schema Update**

```python
class ChatRequest(BaseModel):
    # ... existing fields
    image_size: Optional[str] = "1024x1024"  # Image generation size
```

**2. Generation Function**

```python
async def generate_image_from_prompt(
    prompt: str,
    model: str = "gpt-image-1",
    image: Optional[str] = None,
    reference_images: Optional[List[str]] = None,
    size: str = "1024x1024"  # NEW parameter
) -> dict:
    images = await image_manager.generate(
        prompt=prompt,
        model=model,
        size=size,  # Use provided size
        quality=quality,
        n=1,
        image=image,
        reference_images=reference_images
    )
```

**3. Endpoint Updates**

```python
# Non-streaming
image_result = await generate_image_from_prompt(
    prompt=request.message,
    model=request.model,
    image=input_image,
    reference_images=reference_images_list,
    size=request.image_size or "1024x1024"
)

# Streaming
image_result = await generate_image_from_prompt(
    prompt=request.message,
    model=request.model,
    image=input_image,
    reference_images=reference_images_list,
    size=request.image_size or "1024x1024"
)
```

## User Interface

### Selector Appearance

**Closed state:**
```
┌─────────────────────────────────┐
│ ⚏ □ Square (1:1) (1024x1024)  │
└─────────────────────────────────┘
```

**Open state:**
```
┌─────────────────────────────────┐
│ ⚏ □ Square (1:1) (1024x1024)  │
└─────────────────────────────────┘
  ┌───────────────────────────────┐
  │ Image Aspect Ratio            │
  ├───────────────────────────────┤
  │ □ Square (1:1)    1024x1024  │ ← Selected
  │ ▭ Landscape (16:9) 1792x1024 │
  │ ▯ Portrait (9:16)  1024x1792 │
  │ ▭ Standard (4:3)   1536x1152 │
  │ ▯ Portrait (3:4)   1152x1536 │
  └───────────────────────────────┘
```

### Header Integration

**When GPT-Image-1 is selected:**
```
┌────────────────────────────────────────────────────────┐
│ 🤖 GPT-Image-1                                         │
│ OpenAI                                                 │
│                                                        │
│  [Ratio Selector] [Deep Research] [New Chat]          │
└────────────────────────────────────────────────────────┘
```

**When other models are selected:**
```
┌────────────────────────────────────────────────────────┐
│ 🤖 GPT-4                                               │
│ OpenAI                                                 │
│                                                        │
│  [Deep Research] [New Chat]                            │
└────────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Square Profile Picture

```
1. Select GPT-Image-1
2. Choose "Square (1:1)" from ratio selector
3. Prompt: "Professional headshot of a business person"
4. Result: 1024x1024 square image
```

### Example 2: Landscape Banner

```
1. Select GPT-Image-1
2. Choose "Landscape (16:9)" from ratio selector
3. Prompt: "Mountain landscape at sunset"
4. Result: 1792x1024 widescreen image
```

### Example 3: Portrait Story

```
1. Select GPT-Image-1
2. Choose "Portrait (9:16)" from ratio selector
3. Prompt: "Fashion model in urban setting"
4. Result: 1024x1792 vertical image
```

### Example 4: Standard Presentation

```
1. Select GPT-Image-1
2. Choose "Standard (4:3)" from ratio selector
3. Prompt: "Infographic about climate change"
4. Result: 1536x1152 traditional format
```

## Size Specifications

### GPT-Image-1 Supported Sizes

**Square:**
- 1024x1024 ✅

**Landscape:**
- 1792x1024 ✅
- 1536x1024 ✅

**Portrait:**
- 1024x1792 ✅
- 1024x1536 ✅

**Standard:**
- 1536x1152 ✅
- 1152x1536 ✅

## Request Flow

```
1. User selects GPT-Image-1
2. Ratio selector appears in header
3. User clicks selector
4. Dropdown shows all ratios
5. User selects "Landscape (16:9)"
6. Store updates: imageRatio='16:9', imageSize='1792x1024'
7. User types prompt and sends
8. Frontend includes image_size in request
9. Backend receives size parameter
10. Passes to image generation API
11. OpenAI generates image at specified size
12. Image returned and displayed
```

## Console Output

**With custom ratio:**
```
💬 Sending chat request:
Model: gpt-image-1 Provider: openai
Image Model: gpt-image-1
Image Size: 1792x1024
🎨 Generating image with model: gpt-image-1
📝 Prompt: Mountain landscape at sunset
Size: 1792x1024
✅ Image generated successfully
```

**Default ratio:**
```
💬 Sending chat request:
Model: gpt-image-1 Provider: openai
Image Size: 1024x1024
🎨 Generating image with model: gpt-image-1
Size: 1024x1024 (default)
```

## Benefits

### ✅ Better Control

**Aspect ratio selection:**
- Choose format for specific use cases
- Match target platform requirements
- Optimize for display context

### ✅ Professional Output

**Format-specific generation:**
- Square for social media
- Landscape for presentations
- Portrait for mobile content
- Standard for traditional displays

### ✅ User Experience

**Visual feedback:**
- Clear ratio indicators
- Size specifications shown
- Only visible for GPT-Image-1
- Intuitive icon representation

## Limitations

### Model-Specific

**Only for GPT-Image-1:**
- DALL-E 3: Fixed sizes only
- DALL-E 2: Different size options
- Other models: Not applicable

### Size Constraints

**API limitations:**
- Must use supported sizes
- Cannot use arbitrary dimensions
- Total pixels may be limited

## Testing

### Test 1: Square Generation

```
1. Select GPT-Image-1
2. Choose Square (1:1)
3. Generate image
4. Verify: 1024x1024 dimensions
```

### Test 2: Landscape Generation

```
1. Select GPT-Image-1
2. Choose Landscape (16:9)
3. Generate image
4. Verify: 1792x1024 dimensions
```

### Test 3: Portrait Generation

```
1. Select GPT-Image-1
2. Choose Portrait (9:16)
3. Generate image
4. Verify: 1024x1792 dimensions
```

### Test 4: Selector Visibility

```
1. Select GPT-4
2. Verify: Ratio selector hidden
3. Select GPT-Image-1
4. Verify: Ratio selector visible
```

### Test 5: Multi-turn with Different Ratios

```
1. Generate square image
2. Change to landscape
3. Refine image
4. Verify: New ratio applied
```

## Summary

### What Was Added

✅ **ImageRatioSelector component** - Visual ratio picker
✅ **Store state** - imageRatio and imageSize
✅ **Backend parameter** - image_size in ChatRequest
✅ **API integration** - Size passed to OpenAI
✅ **5 aspect ratios** - Square, landscape, portrait options

### How to Use

1. **Select GPT-Image-1**
2. **Click ratio selector in header**
3. **Choose desired aspect ratio**
4. **Generate image**
5. **Image created at selected size**

### Benefits

✅ **Flexible output** - Multiple aspect ratios
✅ **Professional results** - Format-specific generation
✅ **Easy to use** - Visual selector with icons
✅ **Context-aware** - Only shows for GPT-Image-1

---

**Status**: ✅ Implemented
**Model**: GPT-Image-1 only
**Ratios**: 5 options (1:1, 16:9, 9:16, 4:3, 3:4)
**Testing**: Ready for testing
