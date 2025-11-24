import { useState } from 'react'
import { Maximize2 } from 'lucide-react'

export default function ImageRatioSelector({ selectedRatio, onRatioChange, disabled = false }) {
  const [isOpen, setIsOpen] = useState(false)

  const ratios = [
    { id: '1:1', label: 'Square (1:1)', size: '1024x1024', icon: '□' },
    { id: '3:2', label: 'Landscape (3:2)', size: '1536x1024', icon: '▭' },
    { id: '2:3', label: 'Portrait (2:3)', size: '1024x1536', icon: '▯' },
  ]

  const currentRatio = ratios.find(r => r.id === selectedRatio) || ratios[0]

  return (
    <div className="relative">
      <button
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
          disabled
            ? 'bg-secondary/50 text-muted-foreground cursor-not-allowed'
            : 'bg-secondary border-border hover:bg-secondary/80'
        }`}
        title={disabled ? 'Only available for GPT-Image-1' : 'Select image aspect ratio'}
      >
        <Maximize2 size={16} />
        <span className="text-sm font-medium">{currentRatio.icon} {currentRatio.label}</span>
        <span className="text-xs text-muted-foreground">({currentRatio.size})</span>
      </button>

      {isOpen && !disabled && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 right-0 z-20 bg-popover border border-border rounded-lg shadow-lg min-w-[280px]">
            <div className="p-2">
              <div className="text-xs font-semibold text-muted-foreground px-2 py-1 mb-1">
                Image Aspect Ratio
              </div>
              {ratios.map((ratio) => (
                <button
                  key={ratio.id}
                  onClick={() => {
                    onRatioChange(ratio.id, ratio.size)
                    setIsOpen(false)
                  }}
                  className={`w-full flex items-center justify-between gap-3 px-3 py-2 rounded-md transition-colors ${
                    ratio.id === selectedRatio
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-secondary'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{ratio.icon}</span>
                    <span className="text-sm font-medium">{ratio.label}</span>
                  </div>
                  <span className="text-xs opacity-70">{ratio.size}</span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
