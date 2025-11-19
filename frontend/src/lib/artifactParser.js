/**
 * Parse artifacts from markdown content
 * Supports special artifact syntax like:
 * ```artifact:type:language:title
 * content here
 * ```
 */

export function parseArtifacts(content) {
  const artifacts = []
  
  // Match artifact code blocks
  const artifactRegex = /```artifact(?::(\w+))?(?::(\w+))?(?::([^\n]+))?\n([\s\S]*?)```/g
  
  let match
  let lastIndex = 0
  let contentWithoutArtifacts = ''
  
  while ((match = artifactRegex.exec(content)) !== null) {
    // Add content before this artifact
    contentWithoutArtifacts += content.slice(lastIndex, match.index)
    
    const [fullMatch, type = 'code', language = 'javascript', title = 'Artifact', artifactContent] = match
    
    artifacts.push({
      id: `artifact-${artifacts.length}`,
      type,
      language,
      title: title.trim(),
      content: artifactContent.trim(),
      filename: `${title.trim().replace(/\s+/g, '_')}.${language}`
    })
    
    // Add a placeholder in the content
    contentWithoutArtifacts += `\n\n📦 **Artifact: ${title.trim()}** (Click to view)\n\n`
    
    lastIndex = match.index + fullMatch.length
  }
  
  // Add remaining content
  contentWithoutArtifacts += content.slice(lastIndex)
  
  return {
    artifacts,
    contentWithoutArtifacts: artifacts.length > 0 ? contentWithoutArtifacts : content
  }
}

/**
 * Detect code blocks that should be treated as artifacts
 * Large code blocks (>20 lines) or specific languages
 */
export function detectCodeArtifacts(content) {
  const artifacts = []
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
  
  let match
  while ((match = codeBlockRegex.exec(content)) !== null) {
    const [, language = 'text', code] = match
    const lines = code.trim().split('\n')
    
    // Only create artifacts for substantial code blocks
    if (lines.length > 20 || ['html', 'python', 'javascript', 'typescript', 'jsx', 'tsx'].includes(language)) {
      artifacts.push({
        id: `code-${artifacts.length}`,
        type: 'code',
        language,
        title: `${language.toUpperCase()} Code`,
        content: code.trim(),
        filename: `code.${language}`
      })
    }
  }
  
  return artifacts
}
