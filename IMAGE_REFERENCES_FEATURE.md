# Image References Feature - GPT-Image-1

## Overview

Integrated OpenAI's image references feature that allows you to upload multiple reference images to influence the style, composition, and aesthetic of generated images. This is exclusive to GPT-Image-1.

**Important:** Multiple image references use `images.edit()` with the `image` parameter as a **list** of file objects, not `images.generate()` with a separate `references` parameter.

```python
# Correct usage for multiple references
result = client.images.edit(
    model="gpt-image-1",
    image=[file1, file2, file3],  # List of file objects
    prompt="Create something with these references"
)
```

## How It Works

### Single Image vs Multiple Images

**Single image uploaded:**
- Used for **image editing**
- Modifies the uploaded image based on prompt
- Example: "Make this more vibrant"

**Multiple images uploaded:**
- Used as **style references**
- Generates new image influenced by reference styles
- Example: "Create a landscape" + [2 reference images]

## Usage

### Basic Reference Generation

**1. Select GPT-Image-1**
**2. Upload 2-5 reference images**
**3. Type your prompt:** `"Create a portrait in this style"`
**4. System uses references to guide generation**

### Example Workflows

#### Workflow 1: Style Transfer

```
1. Upload 3 images with similar art style
2. Prompt: "Create a mountain landscape"
3. Result: Mountain landscape in the style of references
```

#### Workflow 2: Composition Guide

```
1. Upload 2 images with desired composition
2. Prompt: "Generate a product photo"
3. Result: Product photo with similar composition
```

#### Workflow 3: Color Palette

```
1. Upload images with desired color scheme
2. Prompt: "Create an abstract artwork"
3. Result: Artwork using reference color palette
```

## Implementation

### Backend Changes

**1. Updated `image_providers.py`:**
```python
async def generate(
    self,
    prompt: str,
    model: str = "dall-e-3",
    image: Optional[str] = None,
    reference_images: Optional[List[str]] = None  # NEW!
) -> List[dict]:
```

**2. Image references handling:**
```python
elif reference_images and model == "gpt-image-1":
    # Convert base64 to file objects
    image_refs = []
    for idx, ref_img in enumerate(reference_images):
        ref_bytes = base64.b64decode(ref_img)
        ref_file = io.BytesIO(ref_bytes)
        ref_file.name = f"reference_{idx}.png"
        image_refs.append(ref_file)
    
    # Call API with references using images.edit()
    # Multiple images are passed as a list to the 'image' parameter
    params = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "image": image_refs,  # List of reference images
        "size": size,
        "n": n
    }
    
    response = await self.client.images.edit(**params)
```

**3. Updated `routes/chat.py`:**
```python
if request.images:
    if len(request.images) == 1:
        # Single image - use for editing
        input_image = request.images[0]
    else:
        # Multiple images - use as references
        if request.model == "gpt-image-1":
            reference_images_list = request.images
        else:
            # Other models don't support references
            input_image = request.images[0]
```

### Frontend Support

**Already works!**
- ChatInput allows multiple image uploads
- System automatically detects multiple images
- Routes them as references for GPT-Image-1

## Features

### ✅ Automatic Detection

**System automatically:**
- Detects number of uploaded images
- Routes single image to editing
- Routes multiple images to references
- Only for GPT-Image-1 (other models use first image)

### ✅ Model-Specific

**GPT-Image-1:**
- ✅ Supports image references
- ✅ 1-5 reference images recommended
- ✅ Influences style, composition, colors

**DALL-E 3:**
- ❌ No reference support
- Uses first image only (if any)

**DALL-E 2:**
- ❌ No reference support
- Uses first image for editing

### ✅ Console Feedback

**With references:**
```
🎨 Image model selected: gpt-image-1
📝 Generating image from prompt: Create a landscape...
🎨 Using 3 images as references
🎨 Using image references for GPT-Image-1
   Number of reference images: 3
📤 Calling OpenAI images.generate with image references
   Parameters: model=gpt-image-1, size=1024x1024, quality=auto, refs=3
✅ Image generated successfully
```

**Without references:**
```
🎨 Image model selected: gpt-image-1
📝 Generating image from prompt: A mountain...
📤 Calling OpenAI images.generate with params: {...}
✅ Image generated successfully
```

## Use Cases

### 1. Brand Consistency

**Upload brand style guides:**
```
References: [logo, brand colors, design examples]
Prompt: "Create a marketing banner"
Result: Banner matching brand style
```

### 2. Artistic Style

**Upload artwork in desired style:**
```
References: [impressionist paintings]
Prompt: "Create a garden scene"
Result: Garden in impressionist style
```

### 3. Photography Style

**Upload reference photos:**
```
References: [professional portraits]
Prompt: "Generate a headshot"
Result: Headshot matching reference style
```

### 4. Color Schemes

**Upload images with desired colors:**
```
References: [sunset photos]
Prompt: "Create an abstract composition"
Result: Abstract with sunset colors
```

### 5. Composition Templates

**Upload composition examples:**
```
References: [rule of thirds examples]
Prompt: "Generate a landscape"
Result: Landscape with similar composition
```

## Best Practices

### Number of References

**Recommended:** 2-5 images
- 1 image: Minimal influence
- 2-3 images: Good balance
- 4-5 images: Strong influence
- 6+ images: May dilute effect

### Reference Quality

**Use high-quality references:**
- ✅ Clear, well-lit images
- ✅ Consistent style across references
- ✅ High resolution
- ❌ Blurry or low-quality images

### Reference Consistency

**For best results:**
- Use references with similar style
- Consistent color palette
- Similar composition
- Cohesive aesthetic

### Prompt Clarity

**Be specific:**
```
❌ "Make something"
✅ "Create a portrait in this style"
✅ "Generate a landscape with these colors"
✅ "Design a product photo like these examples"
```

## Limitations

### Model Support

**Only GPT-Image-1:**
- DALL-E 3: No support
- DALL-E 2: No support
- Other models: No support

### Reference Count

**API limits:**
- Minimum: 1 reference
- Maximum: Likely 5-10 (check API docs)
- Recommended: 2-5 for best results

### File Size

**Per image:**
- Max: 4MB per reference
- Format: PNG, JPEG, WebP
- Total: All references combined

## Testing

### Test 1: Basic References

1. Select "GPT-Image-1"
2. Upload 2 similar style images
3. Type: `"Create a landscape"`
4. **Verify:**
   - ✅ Console shows "Using 2 images as references"
   - ✅ Generated image reflects reference style
   - ✅ No errors

### Test 2: Single Image (Editing)

1. Select "GPT-Image-1"
2. Upload 1 image
3. Type: `"Make it more vibrant"`
4. **Verify:**
   - ✅ Console shows "Using user-uploaded image for editing"
   - ✅ Image is edited, not referenced
   - ✅ Original image modified

### Test 3: Multiple Images with DALL-E 3

1. Select "DALL-E 3"
2. Upload 3 images
3. Type: `"Create something"`
4. **Verify:**
   - ✅ Console shows "Using first uploaded image"
   - ✅ Only first image used
   - ✅ References not supported message

### Test 4: Streaming with References

1. Enable streaming
2. Select "GPT-Image-1"
3. Upload 3 references
4. Generate
5. **Verify:**
   - ✅ Shows "Using 3 reference images..."
   - ✅ Generation completes
   - ✅ Style matches references

## Console Output Examples

### With 3 References

```
🎨 Image model selected: gpt-image-1
📝 Generating image from prompt: Create a portrait...
🎨 Using 3 images as references
🎨 Using image references for GPT-Image-1
   Number of reference images: 3
📤 Calling OpenAI images.generate with image references
   Parameters: model=gpt-image-1, size=1024x1024, quality=auto, refs=3
📥 OpenAI response type: <class 'openai.types.images_response.ImagesResponse'>
✅ Image generated successfully
```

### Single Image (Editing)

```
🎨 Image model selected: gpt-image-1
📝 Generating image from prompt: Make it brighter...
🖼️ Using user-uploaded image for editing
✅ Using gpt-image-1 native image editing
📷 Using images.edit for gpt-image-1 image editing
📤 Calling OpenAI images.edit with GPT-Image-1
✅ Image generated successfully
```

## Comparison

### Without References

```
Prompt: "Create a portrait"
Result: Generic portrait based on prompt alone
```

### With References

```
Prompt: "Create a portrait"
References: [3 impressionist paintings]
Result: Portrait in impressionist style
```

## Summary

### What Was Added

✅ **Image references support** - Multiple images as style guides
✅ **Automatic detection** - Single vs multiple images
✅ **GPT-Image-1 exclusive** - Only model that supports it
✅ **Both endpoints** - Streaming and non-streaming
✅ **Console feedback** - Clear logging

### How to Use

1. **Select GPT-Image-1**
2. **Upload 2-5 reference images**
3. **Type your prompt**
4. **System uses references automatically**

### Benefits

✅ **Style consistency** - Match reference aesthetics
✅ **Brand alignment** - Use brand guidelines
✅ **Artistic control** - Guide generation style
✅ **Color matching** - Use reference palettes
✅ **Composition guidance** - Influence layout

---

**Status**: ✅ Implemented
**Model**: GPT-Image-1 only
**References**: 1-5 images recommended
**Testing**: Ready for testing
