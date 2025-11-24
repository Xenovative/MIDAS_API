import { Loader2 } from 'lucide-react'

export default function ImageLoadingPlaceholder({ 
  message = "Generating image...",
  previousImage = null 
}) {
  return (
    <div className="relative inline-block my-4">
      <div 
        className="relative flex items-center justify-center bg-secondary/50 border-2 border-dashed border-border rounded-lg overflow-hidden"
        style={{
          width: '512px',
          height: '512px',
          maxWidth: '100%'
        }}
      >
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
