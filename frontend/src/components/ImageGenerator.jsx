import { useState, useEffect } from 'react'
import { Wand2, Loader2, Download } from 'lucide-react'
import { generationApi } from '../lib/api'

export default function ImageGenerator() {
  const [prompt, setPrompt] = useState('')
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)
  const [size, setSize] = useState('1024x1024')
  const [quality, setQuality] = useState('standard')
  const [style, setStyle] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImages, setGeneratedImages] = useState([])

  useEffect(() => {
    loadModels()
  }, [])

  // Ensure size/quality always stay valid for the active model
  useEffect(() => {
    if (!selectedModel) return

    if (!selectedModel.sizes.includes(size)) {
      setSize(selectedModel.sizes[0])
    }

    if (!selectedModel.qualities.includes(quality)) {
      setQuality(selectedModel.qualities[0] || 'standard')
    }

    if (!selectedModel.supports_style) {
      setStyle('')
    } else if (style && !selectedModel.styles.includes(style)) {
      setStyle('')
    }
  }, [selectedModel])

  const loadModels = async () => {
    try {
      const response = await generationApi.listImageModels()
      setAvailableModels(response.data.models)
      if (response.data.models.length > 0) {
        const firstModel = response.data.models[0]
        setSelectedModel(firstModel)
        setSize(firstModel.sizes[0] || '1024x1024')
        setQuality(firstModel.qualities[0] || 'standard')
      }
    } catch (error) {
      console.error('Failed to load image models:', error)
    }
  }

  const handleGenerate = async () => {
    if (!prompt.trim() || !selectedModel) return

    setIsGenerating(true)
    try {
      const safeQuality = selectedModel.qualities.includes(quality)
        ? quality
        : (selectedModel.qualities[0] || 'standard')

      const response = await generationApi.generateImage({
        prompt,
        model: selectedModel.id,
        size,
        quality: safeQuality,
        style: style || undefined,
        n: 1
      })

      setGeneratedImages([...response.data.images, ...generatedImages])
    } catch (error) {
      console.error('Image generation error:', error)
      alert('Failed to generate image: ' + (error.response?.data?.detail || error.message))
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = (imageUrl, index) => {
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = `generated-image-${index + 1}.png`
    link.click()
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold mb-4">Image Generation</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the image you want to generate..."
            className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px]"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Model</label>
            <select
              value={selectedModel?.id || ''}
              onChange={(e) => {
                const model = availableModels.find(m => m.id === e.target.value)
                setSelectedModel(model)
                if (model && model.sizes.length > 0) {
                  setSize(model.sizes[0])
                }
                if (model && model.qualities.length > 0) {
                  setQuality(model.qualities[0])
                }
                setStyle('')
              }}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {availableModels.map(model => (
                <option key={model.id} value={model.id}>
                  {model.name} ({model.provider})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Size</label>
            <select
              value={size}
              onChange={(e) => setSize(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {selectedModel?.sizes.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">

          <div>
            <label className="block text-sm font-medium mb-2">Quality</label>
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {selectedModel?.qualities.map(q => (
                <option key={q} value={q}>{q.charAt(0).toUpperCase() + q.slice(1)}</option>
              ))}
            </select>
          </div>

          {selectedModel?.supports_style && selectedModel.styles.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-2">Style (Optional)</label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">None</option>
                {selectedModel.styles.map(s => (
                  <option key={s} value={s}>{s.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating || !prompt.trim()}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {isGenerating ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Wand2 size={20} />
              Generate Image
            </>
          )}
        </button>
      </div>

      {generatedImages.length > 0 && (
        <div>
          <h4 className="font-medium mb-3">Generated Images</h4>
          <div className="grid grid-cols-2 gap-4">
            {generatedImages.map((img, index) => (
              <div key={index} className="border border-border rounded-lg overflow-hidden">
                <img
                  src={img.url}
                  alt={img.revised_prompt || 'Generated image'}
                  className="w-full h-auto"
                />
                <div className="p-3 bg-muted/30">
                  {img.revised_prompt && (
                    <p className="text-xs text-muted-foreground mb-2">
                      {img.revised_prompt}
                    </p>
                  )}
                  <button
                    onClick={() => handleDownload(img.url, index)}
                    className="flex items-center gap-2 text-sm px-3 py-1.5 bg-primary text-primary-foreground rounded hover:opacity-90 transition-opacity"
                  >
                    <Download size={14} />
                    Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
