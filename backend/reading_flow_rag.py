"""
Reading Flow RAG - Makes LLM read documents like a person
Provides sequential context and natural reading flow
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import Document, DocumentChunk


class ReadingFlowRAG:
    """Enhanced RAG that provides reading-like context"""
    
    @staticmethod
    async def get_reading_context(
        db: AsyncSession,
        matched_chunks: List[Dict],
        context_window: int = 5,
        max_total_chunks: int = 50
    ) -> List[Dict]:
        """
        Get reading context around matched chunks
        
        Args:
            matched_chunks: List of matched chunks from vector search
            context_window: Number of chunks before/after to include
            max_total_chunks: Maximum total chunks to return
        
        Returns:
            List of chunks with reading flow context
        """
        if not matched_chunks:
            return []
        
        # Group by document
        doc_groups = {}
        for chunk in matched_chunks:
            doc_id = chunk['document_id']
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(chunk)
        
        # For each document, get continuous reading sections
        reading_sections = []
        
        for doc_id, chunks in doc_groups.items():
            # Sort chunks by index
            chunks.sort(key=lambda x: x['chunk_index'])
            
            # Get continuous sections with context
            sections = await ReadingFlowRAG._get_continuous_sections(
                db, doc_id, chunks, context_window
            )
            
            reading_sections.extend(sections)
        
        # Limit total chunks
        if len(reading_sections) > max_total_chunks:
            # Keep highest similarity chunks
            reading_sections.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            reading_sections = reading_sections[:max_total_chunks]
            # Re-sort by document and position
            reading_sections.sort(key=lambda x: (x['document_id'], x['chunk_index']))
        
        return reading_sections
    
    @staticmethod
    async def _get_continuous_sections(
        db: AsyncSession,
        doc_id: str,
        matched_chunks: List[Dict],
        context_window: int
    ) -> List[Dict]:
        """Get continuous reading sections for a document"""
        
        # Determine range to fetch
        chunk_indices = [c['chunk_index'] for c in matched_chunks]
        min_idx = min(chunk_indices)
        max_idx = max(chunk_indices)
        
        # Expand range with context window
        start_idx = max(0, min_idx - context_window)
        end_idx = max_idx + context_window
        
        # Fetch all chunks in range
        query = select(DocumentChunk, Document).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            DocumentChunk.document_id == doc_id,
            DocumentChunk.chunk_index >= start_idx,
            DocumentChunk.chunk_index <= end_idx
        ).order_by(DocumentChunk.chunk_index)
        
        result = await db.execute(query)
        chunks_with_docs = result.all()
        
        # Build continuous section
        continuous_chunks = []
        matched_indices = set(chunk_indices)
        
        for chunk, doc in chunks_with_docs:
            is_matched = chunk.chunk_index in matched_indices
            
            # Find original match for similarity score
            similarity = 0.0
            for matched in matched_chunks:
                if matched['chunk_index'] == chunk.chunk_index:
                    similarity = matched['similarity']
                    break
            
            # If not matched, assign lower similarity based on distance
            if not is_matched:
                # Find closest match
                distances = [abs(chunk.chunk_index - idx) for idx in matched_indices]
                min_distance = min(distances) if distances else 1
                # Decay similarity based on distance
                closest_match = max(matched_chunks, key=lambda x: x['similarity'])
                similarity = closest_match['similarity'] * (0.9 ** min_distance)
            
            continuous_chunks.append({
                'chunk_id': chunk.id,
                'document_id': doc.id,
                'filename': doc.filename,
                'content': chunk.content,
                'similarity': similarity,
                'chunk_index': chunk.chunk_index,
                'is_matched': is_matched,
                'is_context': not is_matched,
                'section_start': chunk.chunk_index == start_idx,
                'section_end': chunk.chunk_index == end_idx
            })
        
        return continuous_chunks
    
    @staticmethod
    def format_reading_context(chunks: List[Dict]) -> str:
        """
        Format chunks as natural reading flow
        
        Args:
            chunks: List of chunks with reading context
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        # Calculate total document coverage
        total_chunks_retrieved = len(chunks)
        unique_docs = len(set(c['filename'] for c in chunks))
        
        lines = []
        lines.append("=== COMPLETE DOCUMENT CONTEXT ===\n")
        lines.append(f"📚 Retrieved {total_chunks_retrieved} sections from {unique_docs} document(s)")
        lines.append("📖 This represents substantial portions of the uploaded document(s)")
        lines.append("✅ You have access to comprehensive context from the full document")
        lines.append("\nBelow is the relevant content presented in reading order:")
        lines.append("Key sections are marked with relevance scores.\n")
        
        # Group by document
        current_doc = None
        section_num = 0
        
        for chunk in chunks:
            # Document header
            if chunk['filename'] != current_doc:
                if current_doc is not None:
                    lines.append("\n" + "="*60 + "\n")
                
                current_doc = chunk['filename']
                lines.append(f"📖 Reading from: {current_doc}\n")
                section_num = 0
            
            # Section marker
            if chunk.get('section_start'):
                section_num += 1
                lines.append(f"\n--- Section {section_num} (Starting at chunk #{chunk['chunk_index']}) ---\n")
            
            # Chunk content with markers
            relevance = int(chunk['similarity'] * 100)
            
            if chunk.get('is_matched'):
                # Highlight matched chunks
                lines.append(f"🎯 [HIGHLY RELEVANT - {relevance}%] Chunk #{chunk['chunk_index']}")
                lines.append(f">>> {chunk['content']}\n")
            else:
                # Context chunks
                lines.append(f"📄 [Context - {relevance}%] Chunk #{chunk['chunk_index']}")
                lines.append(f"{chunk['content']}\n")
        
        lines.append("\n" + "="*60)
        lines.append("\n=== END OF DOCUMENT CONTEXT ===\n")
        lines.append(f"\n📊 Summary: You have {total_chunks_retrieved} sections providing comprehensive coverage")
        lines.append("\nIMPORTANT INSTRUCTIONS:")
        lines.append("- You have access to SUBSTANTIAL portions of the complete document(s)")
        lines.append("- The above sections represent the most relevant parts based on the query")
        lines.append("- Read sequentially and synthesize across all sections")
        lines.append("- Pay special attention to sections marked 🎯 HIGHLY RELEVANT")
        lines.append("- DO NOT claim you only have 'snippets' or 'limited access'")
        lines.append("- You have enough context to provide comprehensive answers")
        
        return "\n".join(lines)
    
    @staticmethod
    def detect_document_structure(content: str) -> Dict:
        """
        Detect document structure (chapters, sections, etc.)
        
        Args:
            content: Document text content
        
        Returns:
            Dictionary with structure information
        """
        structure = {
            'has_chapters': False,
            'has_sections': False,
            'has_numbered_sections': False,
            'chapter_markers': [],
            'section_markers': []
        }
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detect chapters
            if any(marker in line_stripped.lower() for marker in ['chapter ', 'chapter:', 'chapter.']):
                structure['has_chapters'] = True
                structure['chapter_markers'].append(i)
            
            # Detect sections
            if line_stripped.startswith('#') or any(marker in line_stripped.lower() for marker in ['section ', 'section:', '§']):
                structure['has_sections'] = True
                structure['section_markers'].append(i)
            
            # Detect numbered sections (1., 2., etc.)
            if line_stripped and line_stripped[0].isdigit() and '.' in line_stripped[:5]:
                structure['has_numbered_sections'] = True
        
        return structure


# Global instance
reading_flow_rag = ReadingFlowRAG()
