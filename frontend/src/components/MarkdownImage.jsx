import { useState } from 'react'
import { Maximize2, Download } from 'lucide-react'
import ImageViewer from './ImageViewer'

export default function MarkdownImage({ src, alt, ...props }) {
  const [showViewer, setShowViewer] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  const handleDownload = async (e) => {
    e.stopPropagation()
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
      window.open(src, '_blank')
    }
  }

  return (
    <>
      <div 
        className="relative inline-block group my-4"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <img
          src={src}
          alt={alt}
          {...props}
          className="rounded-lg shadow-lg border border-border cursor-pointer"
          onClick={() => setShowViewer(true)}
          style={{
            maxWidth: 'min(100%, 768px)',
            maxHeight: '600px',
            objectFit: 'contain',
            display: 'block'
          }}
        />
        
        {/* Overlay buttons */}
        {isHovered && (
          <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => setShowViewer(true)}
              className="p-2 bg-background/90 hover:bg-background rounded-lg shadow-lg transition-colors"
              title="View full size"
            >
              <Maximize2 size={16} />
            </button>
            <button
              onClick={handleDownload}
              className="p-2 bg-background/90 hover:bg-background rounded-lg shadow-lg transition-colors"
              title="Download image"
            >
              <Download size={16} />
            </button>
          </div>
        )}
      </div>

      {showViewer && (
        <ImageViewer
          src={src}
          alt={alt}
          onClose={() => setShowViewer(false)}
        />
      )}
    </>
  )
}
