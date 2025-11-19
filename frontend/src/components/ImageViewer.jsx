import { X, Download, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { useState } from 'react'

export default function ImageViewer({ src, alt, onClose }) {
  const [zoom, setZoom] = useState(1)

  const handleDownload = async () => {
    try {
      const response = await fetch(src)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = alt || 'image.png'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      // Fallback: open in new tab
      window.open(src, '_blank')
    }
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5))
  const handleResetZoom = () => setZoom(1)

  return (
    <div 
      className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center"
      onClick={onClose}
    >
      {/* Controls */}
      <div className="absolute top-4 right-4 flex gap-2 z-10">
        <button
          onClick={(e) => {
            e.stopPropagation()
            handleZoomOut()
          }}
          className="p-2 bg-background/80 hover:bg-background rounded-lg transition-colors"
          title="Zoom out"
        >
          <ZoomOut size={20} />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            handleResetZoom()
          }}
          className="p-2 bg-background/80 hover:bg-background rounded-lg transition-colors"
          title="Reset zoom"
        >
          <Maximize2 size={20} />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            handleZoomIn()
          }}
          className="p-2 bg-background/80 hover:bg-background rounded-lg transition-colors"
          title="Zoom in"
        >
          <ZoomIn size={20} />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation()
            handleDownload()
          }}
          className="p-2 bg-background/80 hover:bg-background rounded-lg transition-colors"
          title="Download image"
        >
          <Download size={20} />
        </button>
        <button
          onClick={onClose}
          className="p-2 bg-background/80 hover:bg-background rounded-lg transition-colors"
          title="Close"
        >
          <X size={20} />
        </button>
      </div>

      {/* Zoom indicator */}
      <div className="absolute top-4 left-4 px-3 py-2 bg-background/80 rounded-lg text-sm">
        {Math.round(zoom * 100)}%
      </div>

      {/* Image */}
      <div 
        className="max-w-[90vw] max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <img
          src={src}
          alt={alt}
          style={{ 
            transform: `scale(${zoom})`,
            transformOrigin: 'center',
            transition: 'transform 0.2s ease-out'
          }}
          className="max-w-none"
        />
      </div>
    </div>
  )
}
