import { useState } from 'react'
import { X, Copy, Check, Download, Maximize2, Minimize2, Play, Code } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function ArtifactViewer({ artifact, onClose }) {
  const [copied, setCopied] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const [viewMode, setViewMode] = useState('preview') // 'preview' or 'code'

  if (!artifact) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Copy failed:', error)
    }
  }

  const handleDownload = () => {
    const blob = new Blob([artifact.content], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = artifact.filename || `artifact.${artifact.language || 'txt'}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  const canRunCode = () => {
    const runnableLanguages = ['javascript', 'js', 'html', 'jsx', 'tsx']
    return runnableLanguages.includes(artifact.language?.toLowerCase())
  }

  const generateRunnableHTML = () => {
    const lang = artifact.language?.toLowerCase()
    
    if (lang === 'html') {
      return artifact.content
    }
    
    // For JavaScript/JSX, wrap in HTML
    if (['javascript', 'js', 'jsx', 'tsx'].includes(lang)) {
      return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body { margin: 0; padding: 20px; font-family: system-ui, -apple-system, sans-serif; }
    * { box-sizing: border-box; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    ${artifact.content}
    
    // Auto-render if there's a default export or component
    if (typeof App !== 'undefined') {
      ReactDOM.render(<App />, document.getElementById('root'));
    }
  </script>
</body>
</html>`
    }
    
    return artifact.content
  }

  const renderContent = () => {
    const isRunnable = canRunCode()
    
    switch (artifact.type) {
      case 'code':
        // Show preview mode for runnable code
        if (isRunnable && viewMode === 'preview') {
          return (
            <iframe
              srcDoc={generateRunnableHTML()}
              className="w-full h-full border-0 rounded-lg bg-white"
              style={{ minHeight: isMaximized ? 'calc(100vh - 200px)' : '500px' }}
              sandbox="allow-scripts"
              title={artifact.title}
            />
          )
        }
        
        // Show code view
        return (
          <SyntaxHighlighter
            language={artifact.language || 'javascript'}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
              maxHeight: isMaximized ? 'calc(100vh - 200px)' : '500px',
              overflow: 'auto'
            }}
            showLineNumbers
          >
            {artifact.content}
          </SyntaxHighlighter>
        )
      
      case 'html':
        return (
          <iframe
            srcDoc={artifact.content}
            className="w-full h-full border-0 rounded-lg bg-white"
            style={{ minHeight: isMaximized ? 'calc(100vh - 200px)' : '500px' }}
            sandbox="allow-scripts"
            title={artifact.title}
          />
        )
      
      case 'markdown':
        return (
          <div className="prose prose-sm max-w-none p-4 bg-muted rounded-lg overflow-auto"
               style={{ maxHeight: isMaximized ? 'calc(100vh - 200px)' : '500px' }}>
            <pre className="whitespace-pre-wrap">{artifact.content}</pre>
          </div>
        )
      
      case 'mermaid':
        return (
          <div className="p-4 bg-white rounded-lg overflow-auto"
               style={{ maxHeight: isMaximized ? 'calc(100vh - 200px)' : '500px' }}>
            <pre className="text-sm">{artifact.content}</pre>
            <p className="text-xs text-muted-foreground mt-4">
              Mermaid diagram - copy and paste into a Mermaid viewer
            </p>
          </div>
        )
      
      default:
        return (
          <pre className="p-4 bg-muted rounded-lg overflow-auto text-sm"
               style={{ maxHeight: isMaximized ? 'calc(100vh - 200px)' : '500px' }}>
            {artifact.content}
          </pre>
        )
    }
  }

  return (
    <div className={`fixed ${isMaximized ? 'inset-4' : 'right-4 top-20 bottom-4 w-1/2'} bg-background border border-border rounded-lg shadow-2xl z-40 flex flex-col`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold truncate">{artifact.title || 'Artifact'}</h3>
          {artifact.description && (
            <p className="text-xs text-muted-foreground truncate">{artifact.description}</p>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          {/* Language/Type Badge */}
          {artifact.language && (
            <span className="px-2 py-1 text-xs bg-primary/10 text-primary rounded">
              {artifact.language}
            </span>
          )}
          
          {/* Preview/Code Toggle for runnable code */}
          {canRunCode() && (
            <div className="flex border border-border rounded overflow-hidden">
              <button
                onClick={() => setViewMode('preview')}
                className={`px-3 py-1 text-xs transition-colors ${
                  viewMode === 'preview' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-accent'
                }`}
                title="Preview"
              >
                <Play size={14} />
              </button>
              <button
                onClick={() => setViewMode('code')}
                className={`px-3 py-1 text-xs transition-colors ${
                  viewMode === 'code' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'hover:bg-accent'
                }`}
                title="Code"
              >
                <Code size={14} />
              </button>
            </div>
          )}
          
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="p-2 hover:bg-accent rounded transition-colors"
            title="Copy to clipboard"
          >
            {copied ? <Check size={18} className="text-green-600" /> : <Copy size={18} />}
          </button>
          
          {/* Download Button */}
          <button
            onClick={handleDownload}
            className="p-2 hover:bg-accent rounded transition-colors"
            title="Download"
          >
            <Download size={18} />
          </button>
          
          {/* Maximize/Minimize Button */}
          <button
            onClick={() => setIsMaximized(!isMaximized)}
            className="p-2 hover:bg-accent rounded transition-colors"
            title={isMaximized ? 'Minimize' : 'Maximize'}
          >
            {isMaximized ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded transition-colors"
            title="Close"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden p-4">
        {renderContent()}
      </div>
    </div>
  )
}
